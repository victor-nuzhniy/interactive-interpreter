import re
import copy


def tokenize(expression):
    if expression == "":
        return []
    regex = re.compile(r"\s*(=>|[0-9]*\.?[0-9]+|[-+*/%=()]|[A-Za-z_][A-Za-z0-9_]*)\s*")
    tokens = regex.findall(expression)
    return [s for s in tokens if not s.isspace()]


class Interpreter:
    def __init__(self):
        self.full_identifier = re.compile(r'[A-Za-z_][A-Za-z0-9_]*|[*/%+\-=]|[\-]?\d+([.]\d+)?')
        self.identifier = re.compile('[A-Za-z_][A-Za-z0-9_]*')
        self.operator = re.compile(r'[*/%+\-=]')
        self.operator_1 = re.compile(r'[*/%]')
        self.operator_2 = re.compile(r'[+-]')
        self.operator_3 = re.compile(r'[=]')
        self.expression = re.compile(r'\([a-zA-Z0-9*/%+-=_ .]+\)')
        self.number = re.compile(r'-?[0-9]*\.?[0-9]+')
        self.space = re.compile(r' +')
        self.interpreter_dict = {}
        self.operator_dict = {'*': self.multiple,
                              '/': self.divide,
                              '%': self.divide_part,
                              '+': self.add,
                              '-': self.subtract,
                              '=': self.assign}
        self.inp = ''
        self.result = ''
        self.arg_1 = '0'
        self.arg_2 = '1'
        self.func_i = 0
        self.func_flag = 0
        self.stack = []
        self.error = None

    def input(self, expression):
        tokens = tokenize(expression)
        self.inp = ' '.join(tokens)
        self.parsing_input()
        if self.error is not None:
            self.result = self.error
            self.error = None
            raise KeyError(self.result)
        if re.fullmatch(r'[\-]?\d+([.]0+)?', self.result):
            number = self.result.split('.')
            self.result = number[0]
            return int(self.result)
        return self.result

    def parsing_input(self):
        if self.inp[0:2] == 'fn':
            help_str = self.inp.split(' => ')
            function_name_list = tokenize(help_str[0])
            if self.identifier.fullmatch(function_name_list[1]) is None:
                self.error = 'input: \'' + self.inp + '\''
                return None
            if self.interpreter_dict.get(function_name_list[1]) is not None:
                if type(self.interpreter_dict[function_name_list[1]]) is not list:
                    self.error = 'input: \'' + self.inp + '\''
                    return None
            self.interpreter_dict[function_name_list[1]] = []
            check_list = [function_name_list[1]]
            function_arg_set = set()
            i = 2
            while i < len(function_name_list):
                if self.identifier.fullmatch(function_name_list[i]) is None:
                    self.error = 'input: \'' + self.inp + '\''
                    self.interpreter_dict.pop(function_name_list[1])
                    return self.result
                self.interpreter_dict[function_name_list[1]].append(function_name_list[i])
                if function_name_list[i] in function_arg_set:
                    self.error = 'input: \'' + self.inp + '\''
                    self.interpreter_dict.pop(function_name_list[1])
                    return ''
                function_arg_set.add(function_name_list[i])
                check_list.append('1')
                i += 1
            function_expression_list = tokenize(help_str[1])
            for token in function_expression_list:
                if self.identifier.fullmatch(token):
                    if token not in function_arg_set:
                        self.error = 'input: \'' + self.inp + '\''
                        self.interpreter_dict.pop(function_name_list[1])
                        return None
            self.interpreter_dict[function_name_list[1]].append(help_str[1])
            function_check = ' '.join(check_list)
            self.find_result(function_check)
            if self.error is not None:
                self.interpreter_dict.pop(function_name_list[1])
                self.error = 'input: \'' + self.inp + '\''
                return None
            self.result = ''
        elif not self.inp:
            self.result = ''
            return ''
        else:
            return self.find_result(self.inp)

    def find_result_help(self, exp_list, pattern):
        i = 1
        while i < len(exp_list):
            if pattern.fullmatch(exp_list[i]):
                if pattern == self.operator_3:
                    for j in range(1, len(exp_list)):
                        if pattern.fullmatch(exp_list[j]):
                            i = j
                    if (self.interpreter_dict.get(exp_list[i - 1]) is not None
                            and type(self.interpreter_dict[exp_list[i - 1]]) is list):
                        self.error = 'input: \'' + ' '.join(exp_list) + '\''
                        return ''
                    if self.number.fullmatch(exp_list[i - 1]):
                        self.error = 'input: \'' + ' '.join(exp_list) + '\''
                        return ''
                    self.arg_1 = exp_list[i - 1]
                    index = i - 1
                else:
                    exp = self.find_expression(i, exp_list, -1)
                    if self.error is not None:
                        self.error = 'input: \'' + ' '.join(exp_list) + '\''
                        return ''
                    if type(exp) is list:
                        self.arg_1 = self.function(exp)
                        if self.error is not None:
                            return ''
                        if self.arg_1 is None:
                            self.error = 'input: \'' + ' '.join(exp_list) + '\''
                            return ''
                        index = i - len(exp)
                    elif self.number.fullmatch(exp):
                        self.arg_1 = exp
                        index = i - 1
                    else:
                        if self.interpreter_dict.get(exp) is None or type(self.interpreter_dict[exp]) is list:
                            self.error = 'input: \'' + ' '.join(exp_list) + '\''
                            return ''
                        self.arg_1 = self.interpreter_dict[exp]
                        index = i - 1
                exp = self.find_expression(i, exp_list, 1)
                if self.error is not None:
                    self.error = 'input: \'' + ' '.join(exp_list) + '\''
                    return ''
                if type(exp) is list:
                    self.arg_2 = self.function(exp)
                    if self.error is not None:
                        return ''
                    if self.arg_2 is None:
                        self.error = 'input: \'' + ' '.join(exp_list) + '\''
                        return ''
                elif self.number.fullmatch(exp):
                    self.arg_2 = exp
                else:
                    if self.interpreter_dict.get(exp) is None or type(self.interpreter_dict[exp]) is list:
                        self.error = 'input: \'' + ' '.join(exp_list) + '\''
                        return ''
                    self.arg_2 = self.interpreter_dict[exp]
                self.operator_dict[exp_list[i]]()
                exp_list[i], exp_list[i + 1] = None, None
                exp_list[index] = self.result
                exp_list_copy = []
                for k in exp_list:
                    if k is not None:
                        exp_list_copy.append(k)
                exp_list = copy.copy(exp_list_copy)
            else:
                i += 1
        return exp_list

    def find_result(self, help_str):
        if help_str.find('(') == - 1:
            if help_str.find(')') != - 1:
                self.error = 'input: \'' + help_str + '\''
                return ''
            exp_list = help_str.split(' ')
            if self.operator.search(help_str) is None:
                if len(exp_list) == 1 and self.number.fullmatch(exp_list[0]):
                    self.result = exp_list[0]
                elif len(exp_list) == 1 and self.interpreter_dict.get(exp_list[0]) is None:
                    self.error = 'input: \'' + exp_list[0] + '\''
                    return ''
                elif len(exp_list) == 1 and type(self.interpreter_dict[exp_list[0]]) is not list:
                    self.result = self.interpreter_dict[exp_list[0]]
                else:
                    self.result = self.function(exp_list)
                    if self.error is not None:
                        return ''
                return self.result
            while len(exp_list) > 1:
                exp_list = self.find_result_help(exp_list, self.operator_1)
                exp_list = self.find_result_help(exp_list, self.operator_2)
                exp_list = self.find_result_help(exp_list, self.operator_3)
                if self.error is not None:
                    return ''
            return exp_list[0]
        else:
            if help_str.find(')') == - 1:
                self.error = 'input: \'' + help_str + '\''
                return ''
            h_str = self.expression.findall(help_str)
            patt = h_str[0]
            h_list = ''.join([h_str[0][a] for a in range(2, (len(h_str[0]) - 2))])
            h_str[0] = self.find_result(h_list)
            help_str_1 = help_str.replace(patt, h_str[0])
            if self.number.fullmatch(help_str_1) and self.operator.search(help_str_1) is None:
                self.result = help_str_1
                return self.result
            return self.find_result(help_str_1)

    def function(self, function_list):
        if self.number.fullmatch(function_list[0]):
            self.error = self.error = 'input: \'' + ' '.join(function_list) + '\''
            return ''
        for j in function_list:
            if self.identifier.fullmatch(j):
                if self.interpreter_dict.get(j) is None:
                    self.error = self.error = 'input: \'' + ' '.join(function_list) + '\''
                    return ''
            elif self.number.fullmatch(j) is None:
                self.error = self.error = 'input: \'' + ' '.join(function_list) + '\''
                return ''
        if type(self.interpreter_dict[function_list[0]]) is not list:
            self.error = self.error = 'input: \'' + ' '.join(function_list) + '\''
            return ''
        self.stack.append(self.arg_1)
        self.stack.append(self.arg_2)
        func = copy.deepcopy(self.interpreter_dict[function_list[self.func_i]])
        i = 0
        self.func_i += 1
        while self.func_i < len(function_list) and i < len(func) - 1:
            if (self.interpreter_dict.get(function_list[self.func_i]) and
                    type(self.interpreter_dict[function_list[self.func_i]]) is list):
                self.func_flag += 1
                func[-1] = func[-1].replace(func[i], self.function(function_list))
                self.func_flag -= 1
            elif (self.interpreter_dict.get(function_list[self.func_i]) and
                  self.number.fullmatch(self.interpreter_dict[function_list[self.func_i]])):
                func[-1] = func[-1].replace(func[i], self.interpreter_dict[function_list[self.func_i]])
            elif self.number.fullmatch(function_list[self.func_i]):
                func[-1] = func[-1].replace(func[i], function_list[self.func_i])
            else:
                self.error = self.error = 'input: \'' + ' '.join(function_list) + '\''
                return ''
            i += 1
            self.func_i += 1
        if i != len(func) - 1:
            self.error = 'input: \'' + ' '.join(function_list) + '\''
            self.func_i -= 1
            if self.func_flag == 0:
                self.func_i = 0
            return ''
        self.func_i -= 1
        if self.func_flag == 0:
            if self.func_i != len(function_list) - 1:
                self.error = 'input: \'' + ' '.join(function_list) + '\''
                self.func_i = 0
                return ''
            self.func_i = 0
        result = self.find_result(func[-1])
        self.arg_2 = self.stack.pop()
        self.arg_1 = self.stack.pop()
        return result

    def multiple(self):
        self.result = str(float(self.arg_1) * float(self.arg_2))

    def divide(self):
        try:
            float(self.arg_1) / float(self.arg_2)
        except ZeroDivisionError as e:
            self.error = 'ERROR: division by zero'
            return ''
        self.result = str(float(self.arg_1) / float(self.arg_2))

    def divide_part(self):
        self.result = str(float(self.arg_1) % float(self.arg_2))

    def add(self):
        self.result = str(float(self.arg_1) + float(self.arg_2))

    def subtract(self):
        self.result = str(float(self.arg_1) - float(self.arg_2))

    def assign(self):
        if self.interpreter_dict.get(self.arg_2):
            self.interpreter_dict[self.arg_1] = self.interpreter_dict[self.arg_2]
            self.result = self.interpreter_dict[self.arg_2]
        else:
            self.interpreter_dict[self.arg_1] = self.arg_2
            self.result = self.arg_2

    def find_expression(self, j, g_list, sign=1):
        if j == len(g_list) - 1 or j == 0:
            self.error = 'ERROR: invalid syntax'
            return ''
        if len(g_list) == 3:
            return g_list[j + sign]
        i = 1
        if ((j + sign * (i + 1)) >= len(g_list) or (j + sign * (i + 1)) <= 0 or
                self.operator.fullmatch(g_list[j + sign * (i + 1)])):
            result = g_list[j + sign]
            g_list[j + sign] = None
            return result
        else:
            result = []
            while 0 <= j + sign * i < len(g_list) and self.operator.fullmatch(g_list[j + sign * i]) is None:
                result.append(g_list[j + sign * i])
                g_list[j + sign * i] = None
                i += 1
            if sign < 0:
                result.reverse()
            return result