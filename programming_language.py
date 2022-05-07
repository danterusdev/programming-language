import sys
import os
import random
import string
import inspect
from enum import Enum
import platform

random.seed(0)

class Token:
    pass

class Program(Token):
    def __init__(self, tokens):
        self.tokens = tokens
    
class Function(Token):
    def __init__(self, name, tokens, locals, parameter_count):
        self.name = name
        self.tokens = tokens
        self.locals = locals
        self.parameter_count = parameter_count
        
class Use(Token):
    def __init__(self, file):
        self.file = file

class Instruction():
    pass

class Declare(Instruction):
    def __init__(self, name):
        self.name = name
    
class Assign(Instruction):
    def __init__(self, name):
        self.name = name
    
class Retrieve(Instruction):
    def __init__(self, name):
        self.name = name
    
class Constant(Instruction):
    def __init__(self, value):
        self.value = value
    
class Invoke(Instruction):
    def __init__(self, name, argument_count):
        self.name = name
        self.argument_count = argument_count
    
class Return(Instruction):
    def __init__(self, is_value):
        self.is_value = is_value
    
#class Raw(Instruction):
#    def __init__(self, instruction):
#        self.instruction = instruction
    
#class Push(Instruction):
#    def __init__(self):
#        pass

#class Pop(Instruction):
#    def __init__(self):
#        pass

class StartIf(Instruction):
    def __init__(self, id):
        self.id = id

class EndIf(Instruction):
    def __init__(self, id):
        self.id = id

if_id = 0
    
def parse_file(file):
    file = open(file, "r")
    contents = file.read()
    contents = contents.replace("\n", "")
    program = parse(contents, "Program")
    
    for token in program.tokens:
        if isinstance(token, Use):
            program.tokens.extend(parse_file(token.file).tokens)
    return program

def getType(statement):
    if statement.startswith("function "):
        return "Function"
    elif statement.startswith("use "):
        return "Use"
    else:
        return "Statement"
    
def parse(contents, type):
    if type == "Program":
        current_thing = ""
        things = []
        current_indent = 0
        for character in contents:
            if character == ';' and current_indent == 0:
                things.append(parse(current_thing, getType(current_thing)))
                current_thing = ""
            else:
                current_thing += character

            if character == '{':
                current_indent += 1
            elif character == '}':
                current_indent -= 1
        return Program(things)
    elif type == "Function":
        name = contents.split(" ")[1].split("(")[0]
        current_thing = ""
        instructions = []
        current_indent = 0

        arguments_array = []
        arguments = contents[len("function " + name) : contents.index("{")]

        current_argument = ""
        for character in arguments:
            if character == "," or character == ")":
                arguments_array.append(current_argument)
                current_argument = ""

            if (not character == " " and not character == "(" and not character == ")" and not character == ","):
                current_argument += character
        
        if arguments:
            arguments_array.append(current_argument)

        argument_count = 0
        for argument in arguments_array[::-1]:
            if argument:
                instructions.append(Declare(argument))
                argument_count += 1
        
        for character in contents[contents.index("{") + 1 : contents.rindex("}")]:
            if character == ';' and current_indent == 0:
                instructions.extend(parse(current_thing, getType(current_thing)))
                current_thing = ""
            else:
                current_thing += character

            if character == '{':
                current_indent += 1
            elif character == '}':
                current_indent -= 1
                
        locals = []
                
        for instruction in instructions:
            if isinstance(instruction, Declare):
                locals.append(instruction.name)

        if not instructions[-1] is Return:
            instructions.append(Return(False))

        return Function(name, instructions, locals, argument_count)
    elif type == "Use":
        use = contents[contents.index(" ") + 1 : len(contents)]
        use = use[1 : len(use) - 1]
        return Use(use)
    elif type == "Statement":
        return parse_statement(contents)
        
def parse_statement(contents):
    contents = contents.lstrip()
    instructions = []

    if contents.startswith("variable "):
        name = contents.split(" ")[1]
        instructions.append(Declare(name))

        if contents.find("=") != -1:
            expression = contents[contents.index("=") + 1 : len(contents)]
            expression = expression.lstrip()
            instructions.extend(parse_statement(expression))
            instructions.append(Assign(name))
    elif contents.startswith("return ") or contents == "return":
        return_value_statement = contents[7 : len(contents)]
        if return_value_statement:
            instructions.extend(parse_statement(return_value_statement))
        instructions.append(Return(return_value_statement))
    elif contents[0].isnumeric() or contents[0] == "-":
        instructions.append(Constant(int(contents)))
    elif contents == "true" or contents == "false":
        instructions.append(Constant(contents == "true"))
    elif contents.startswith("\""):
        instructions.append(Constant(contents[1 : len(contents) - 1]))
    #elif contents.startswith("asm "):
    #    instructions.append(Raw(contents[4: len(contents)]))
    #elif contents.startswith("push "):
    #    instructions.extend(parse_statement(contents[5 : len(contents)]))
    #    instructions.append(Push())
    #elif contents.startswith("pop"):
    #    instructions.append(Pop())
    elif contents.startswith("if"):
        instructions.extend(parse_statement(contents[contents.index("(") + 1 : contents.index(")")]))

        current_thing = ""
        current_indent = 0
        instructions2 = []

        global if_id
        id = if_id
        if_id += 1

        instructions.append(StartIf(id))

        for character in contents[contents.index("{") + 1 : contents.rindex("}")]:
            if character == ';' and current_indent == 0:
                instructions2.extend(parse(current_thing, getType(current_thing)))
                current_thing = ""
            else:
                current_thing += character

            if character == '{':
                current_indent += 1
            elif character == '}':
                current_indent -= 1

        instructions.extend(instructions2)

        instructions.append(EndIf(id))
    else:
        if "(" in contents:
            name = contents[0 : contents.index("(")]

            arguments_array = []
            arguments = contents[len(name) + 1 : len(contents) - 1]

            current_argument = ""
            current_parenthesis = 0
            in_quotations = False
            for character in arguments:
                if character == "," and current_parenthesis == 0 and not in_quotations:
                    arguments_array.append(current_argument)
                    current_argument = ""
                elif character == "\"":
                    in_quotations = not in_quotations
                elif character == "(":
                    current_parenthesis += 1
                elif character == ")":
                    current_parenthesis -= 1

                if (not character == " " and not character == ",") or (not current_parenthesis == 0) or (in_quotations):
                    current_argument += character
            
            if arguments:
                arguments_array.append(current_argument)
            
            for parameter in arguments_array[::-1]:
                if parameter:
                    instructions.extend(parse_statement(parameter))
            instructions.append(Invoke(name, len(arguments_array)))
        else:
            instructions.append(Retrieve(contents))
        
    return instructions
    
def create_linux_binary(program, file_name_base):
    
    class AsmProgram:
        def __init__(self, functions, data):
            self.functions = functions
            self.data = data
    
    class AsmFunction:
        def __init__(self, name, instructions):
            self.name = name
            self.instructions = instructions
            
    class AsmData:
        def __init__(self, name, value):
            self.name = name
            self.value = value
    
    asm_program = AsmProgram([], [])

    print_size = AsmFunction("print_size", [])
    print_size.instructions.append("push rbp")
    print_size.instructions.append("mov rbp, rsp")
    print_size.instructions.append("mov rcx, [rbp+16]")
    print_size.instructions.append("push rcx")
    print_size.instructions.append("mov rcx, [rbp+24]")
    print_size.instructions.append("push rcx")
    print_size.instructions.append("pop rdx")
    print_size.instructions.append("pop rsi")
    print_size.instructions.append("mov rdi, 1")
    print_size.instructions.append("mov rax, 1")
    print_size.instructions.append("syscall")
    print_size.instructions.append("mov rsp, rbp")
    print_size.instructions.append("pop rbp")
    print_size.instructions.append("ret")
    asm_program.functions.append(print_size)

    length = AsmFunction("length", [])
    length.instructions.append("push rbp")
    length.instructions.append("mov rbp, rsp")
    length.instructions.append("mov rcx, [rbp+16]")
    length.instructions.append("mov rdi, rcx")
    length.instructions.append("xor rax, rax")
    length.instructions.append("mov rcx, -1")
    length.instructions.append("cld")
    length.instructions.append("repne scasb")
    length.instructions.append("not rcx")
    length.instructions.append("dec rcx")
    length.instructions.append("mov r8, rcx")
    length.instructions.append("mov rsp, rbp")
    length.instructions.append("pop rbp")
    length.instructions.append("ret")
    asm_program.functions.append(length)

    _start = AsmFunction("_start", [])
    _start.instructions.append("push rbp")
    _start.instructions.append("mov rbp, rsp")
    _start.instructions.append("call main")
    _start.instructions.append("mov rax, 60")
    _start.instructions.append("xor rdi, rdi")
    _start.instructions.append("syscall")
    _start.instructions.append("mov rsp, rbp")
    _start.instructions.append("pop rbp")
    _start.instructions.append("ret")
    asm_program.functions.append(_start)

    add = AsmFunction("add", [])
    add.instructions.append("push rbp")
    add.instructions.append("mov rbp, rsp")
    add.instructions.append("mov r8, [rbp+16]")
    add.instructions.append("mov rbx, [rbp+24]")
    add.instructions.append("add r8, rbx")
    add.instructions.append("mov rsp, rbp")
    add.instructions.append("pop rbp")
    add.instructions.append("ret")
    asm_program.functions.append(add)

    subtract = AsmFunction("subtract", [])
    subtract.instructions.append("push rbp")
    subtract.instructions.append("mov rbp, rsp")
    subtract.instructions.append("mov r8, [rbp+16]")
    subtract.instructions.append("mov rcx, [rbp+24]")
    subtract.instructions.append("sub r8, rcx")
    subtract.instructions.append("mov rsp, rbp")
    subtract.instructions.append("pop rbp")
    subtract.instructions.append("ret")
    asm_program.functions.append(subtract)

    malloc = AsmFunction("malloc", [])
    malloc.instructions.append("push rbp")
    malloc.instructions.append("mov rbp, rsp")
    malloc.instructions.append("mov rcx, [rbp+16]")
    malloc.instructions.append("mov rax, [index]")
    malloc.instructions.append("mov rbx, rax")
    malloc.instructions.append("add rbx, rcx")
    malloc.instructions.append("mov [index], rbx")
    malloc.instructions.append("mov r8, memory")
    malloc.instructions.append("add r8, rax")
    malloc.instructions.append("mov rsp, rbp")
    malloc.instructions.append("pop rbp")
    malloc.instructions.append("ret")
    asm_program.functions.append(malloc)

    copy = AsmFunction("copy", [])
    copy.instructions.append("push rbp")
    copy.instructions.append("mov rbp, rsp")
    copy.instructions.append("mov rsi, [rbp+16]")
    copy.instructions.append("mov rdi, [rbp+24]")
    copy.instructions.append("mov rcx, [rbp+32]")
    copy.instructions.append("rep movsb")
    copy.instructions.append("mov rsp, rbp")
    copy.instructions.append("pop rbp")
    copy.instructions.append("ret")
    asm_program.functions.append(copy)

    for token in program.tokens:
        if isinstance(token, Function):
            asm_function = AsmFunction(token.name, [])
            
            asm_function.instructions.append("push rbp")
            asm_function.instructions.append("mov rbp, rsp")

            index_thing = 0

            for instruction in token.tokens:
                if isinstance(instruction, Constant):
                    if isinstance(instruction.value, bool):
                        asm_function.instructions.append("push " + ("1" if instruction.value else "0"))
                    elif isinstance(instruction.value, int):
                        asm_function.instructions.append("push " + str(instruction.value))
                    elif isinstance(instruction.value, str):
                        letters = string.ascii_lowercase

                        printable = set("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
                        name = ''.join(filter(lambda x: x in printable, instruction.value.lower())) + "_" + str(index_thing)
                        index_thing += 1

                        put = []
                        encoded = instruction.value.encode()
                        for index, byte in enumerate(encoded):
                            if byte == 0x6e:
                                if encoded[index - 1] == 0x5c:
                                    put.pop()
                                    put.append("0xa")
                            else:
                                put.append(hex(byte))

                        put_string = ""
                        for thing in put:
                            put_string += thing + ","
    
                        put_string += "0x0"

                        asm_program.data.append(AsmData(name, put_string))
                        asm_function.instructions.append("mov r8, " + name)
                        asm_function.instructions.append("push r8")
                elif isinstance(instruction, Invoke):
                    asm_function.instructions.append("call " + instruction.name)
                    for _ in range(instruction.argument_count):
                        asm_function.instructions.append("pop r9")

                    asm_function.instructions.append("push r8")
                #elif isinstance(instruction, Raw):
                #    asm_function.instructions.append(instruction.instruction)
                elif isinstance(instruction, Assign):
                    asm_function.instructions.append("pop r8")
                    index = token.locals.index(instruction.name)
                    if index <= token.parameter_count - 1:
                        index -= 2
                    asm_function.instructions.append("mov [rbp" + "{:+d}".format(-index * 8 - 8 + 8 * token.parameter_count) + "], r8")
                elif isinstance(instruction, Retrieve):
                    index = token.locals.index(instruction.name)
                    if index <= token.parameter_count - 1:
                        index -= 2
                    asm_function.instructions.append("mov r8, [rbp" + "{:+d}".format(-index * 8 - 8 + 8 * token.parameter_count) + "]")
                    asm_function.instructions.append("push r8")
                elif isinstance(instruction, Return):
                    if instruction.is_value:
                         asm_function.instructions.append("pop r8")

                    asm_function.instructions.append("mov rsp, rbp")
                    asm_function.instructions.append("pop rbp")
                    asm_function.instructions.append("ret")
                elif isinstance(instruction, StartIf):
                    asm_function.instructions.append("pop r8")
                    asm_function.instructions.append("cmp r8, 1")
                    asm_function.instructions.append("jne if_" + str(instruction.id))
                elif isinstance(instruction, EndIf):
                    asm_function.instructions.append("if_" + str(instruction.id) + ":")
                    pass
            asm_program.functions.append(asm_function)

    file = open("build/" + file_name_base + ".asm", "w")

    file.write(inspect.cleandoc("""
        global _start
        section .text
    """))
    file.write("\n")

    for function in asm_program.functions:
        file.write(function.name + ":\n")
        stack_index = 0
        stack_index_max = 0
        for instruction in function.instructions:
            if instruction.startswith("push "):
                stack_index += 1
            elif instruction.startswith("pop "):
                stack_index -= 1

            stack_index_max = max(stack_index, stack_index_max)

        function.instructions.insert(2, "sub rsp, " + str(stack_index_max * 8))
    
        for instruction in function.instructions:
            file.write("   " + instruction + "\n")

    file.write(inspect.cleandoc("""
        section .data
    """))
    file.write("\n")

    for data in asm_program.data:
        file.write(data.name + ": db " + data.value + "\n")

    file.write(inspect.cleandoc("""
        section .bss
        memory: resb 16384
        index: resb 8
    """))

    file.close()

file_name_base = sys.argv[1][0 : sys.argv[1].index(".")]
program = parse_file(sys.argv[1])

format = ""
system = platform.system()

try:
    os.mkdir("build")
except OSError:
    pass

if system == "Windows":
    #format = "win64"
    pass
elif system == "Linux":
    create_linux_binary(program, file_name_base)
    code = os.system("nasm -felf64 build/" + file_name_base + ".asm && ld build/" + file_name_base + ".o -o build/" + file_name_base)

    if "-r" in sys.argv and code == 0:
        os.system("./build/" + file_name_base)
elif system == "Darwin":
    #format = "macho64"
    pass