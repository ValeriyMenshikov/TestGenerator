import requests
import re
from pathlib import Path
import json
from ast import literal_eval
from sys import platform
import subprocess
import sys
import os
import datetime

now = datetime.datetime.now()
now.strftime("%Y-%m-%d_%H_%M")

dd = {}
results = []
temp = ''


class Swagger:
    POST = 'post'
    GET = 'get'
    PUT = 'put'
    DELETE = 'delete'

    def __init__(self, url=None, obj=None, folder=os.path.abspath(os.curdir)):
        if url:
            self.swagger_dict = requests.get(url).json()
        elif obj:
            self.swagger_dict = obj

        self.folder = folder
        self.host_name = os.path.dirname(url)

    # TODO сделать по человечески через проперти
    # def __init__(self, url):
    #     with open(url, errors='ignore', encoding='UTF-8') as f:
    #         self.swagger_dict = json.load(f)

    def create_env(self, requirements_path='config_helper/requirements.txt'):
        folder = os.path.join(self.folder, 'venv')
        if not os.path.exists(os.path.join(folder)):
            subprocess.call([sys.executable, '-m', 'venv', folder])
            if platform == "win32":
                python_interpreter = os.path.join(folder, 'Scripts', 'python.exe')
            else:
                python_interpreter = os.path.join(folder, 'bin', 'python')
            subprocess.call([python_interpreter, '-m', 'pip', 'install', '--upgrade', 'pip'])
            subprocess.call([python_interpreter, '-m', 'pip', 'install', '-r', requirements_path])
        else:
            print("INFO: %s exists." % (folder))

    def all(self):
        """
        Метод для получения всего json сваггера

        :return: Строка с импортами
        """
        return self.swagger_dict

    def methods(self):
        """
        Метод возвращает список всех доступных методов описанных в сваггере

        :return: Все доступные api методы (тип метода, название метода)
        """
        return self._get_endpoint_by_type()

    def version(self):
        """
        Метод возвращает версию сервиса описанного в свагере

        :return: Название сервиса
        """
        return self.swagger_dict['info']['version']

    def service_name(self):
        """
        Метод возвращает название сервиса описанного в свагере

        :return: Название сервиса
        """
        try:
            return self.swagger_dict['info']['title'].split('-')[2].capitalize()
        except IndexError:
            return self.swagger_dict['info']['title'].replace(' ', '')

    def post_methods(self):
        """
        Метод возвращает все post методы описанные в свагере

        :return: post методы (тип метода, название метода)
        """

        return self._get_endpoint_by_type(Swagger.POST)

    def _get_endpoint_by_type(self, method_type=None):
        result = []
        sw = self.swagger_dict['paths']
        for end_point in sw:
            if sw.get(end_point):
                for method in sw[end_point]:
                    tag = sw[end_point][method].get('tags')[0]
                    if method == method_type:
                        result.append({'method': method, 'end_point': end_point, 'tag': tag})
                    elif method_type is None:
                        result.append({'method': method, 'end_point': end_point, 'tag': tag})
                    else:
                        continue
        return result

    def get_methods(self):
        """
        Метод возвращает все get методы описанные в свагере

        :return: get методы (тип метода, название метода)
        """
        return self._get_endpoint_by_type(Swagger.GET)

    def put_methods(self):
        """
        Метод возвращает все put методы описанные в свагере

        :return: put методы (тип метода, название метода)
        """
        return self._get_endpoint_by_type(Swagger.PUT)

    def delete_methods(self):
        """
        Метод возвращает все delete методы описанные в свагере

        :return: delete методы (тип метода, название метода)
        """
        return self._get_endpoint_by_type(Swagger.DELETE)

    def description(self, data):
        """
        Метод для получения описания метода описанного в сваггере

        :param data: Кортеж в формате (тип метода, название метода)
        :return: Описание метода
        """
        data = self._check_input(data)
        method = data["method"]
        end_point = data["end_point"]
        desc = self.swagger_dict['paths'][end_point][method].get('summary')
        if desc:
            return desc.replace('\r\n', '')
        return 'У метода нет описания'

    @staticmethod
    def _check_input(data):
        if isinstance(data, dict) and ('end_point', 'method', 'tag' in data.keys()) and len(data) == 3:
            return data
        else:
            raise TypeError('Data should be one of dict from one of get_methods functions')

    def parameters(self, data):
        data = self._check_input(data)
        method = data["method"]
        end_point = data["end_point"]
        result = {}
        try:
            add = lambda param_type, params: result[param_type].update(
                {params.get("name"): params["schema"].get("type", 'None') if params.get("schema") else params.get("type")})
            if self.swagger_dict['paths'][end_point][method].get("parameters"):
                for path_param in self.swagger_dict['paths'][end_point][method]["parameters"]:
                    result.setdefault(path_param.get("in"), {})
                    if path_param.get("in") == 'path':
                        add('path', path_param)
                    elif path_param.get("in") == 'query':
                        add('query', path_param)
                    elif path_param.get("in") == 'header':
                        add('header', path_param)
                return result
        except KeyError:
            raise KeyError(path_param)

    def status_code(self, data):
        data = self._check_input(data)
        method = data["method"]
        end_point = data["end_point"]
        for code in self.swagger_dict['paths'][end_point][method]["responses"].keys():
            return code

    def _model_dict(self, data):
        m = lambda x: x.split('/')[-1]
        data = self._check_input(data)
        method = data["method"]
        end_point = data["end_point"]
        request_body = self.swagger_dict['paths'][end_point][method].get('requestBody')
        result = {}
        if request_body:
            count = 0
            while True:
                try:
                    if count == 0:
                        model = m(request_body['content']['application/json']['schema']['$ref'])
                    elif count == 1:
                        model = m(request_body['content']['multipart/form-data']['schema']['$ref'])
                    elif count == 2:
                        model = m(
                            request_body['content']['multipart/form-data']['schema']['properties']['name']['$ref'])
                    elif count == 3:
                        model = m(request_body['content']['application/json']['schema']['$ref'])
                    elif count == 4:
                        result = request_body['content']['multipart/form-data']['schema']
                        break
                    else:
                        break
                    for k, v in self.swagger_dict['components']['schemas'][model]['properties'].items():
                        if v.get('type') == 'array' and '$ref' in v.get('items', 'None'):
                            result[k] = [m(v['items']['$ref'])]
                        elif v.get('type') == 'array':
                            result[k] = []
                        else:
                            result[k] = v.get('type', 'None')
                    if count >= 2:
                        break
                except KeyError:
                    count += 1
                    continue
                break
        else:
            return

        return result

    def _model_dict_v2(self, data):
        """
        Вспомогательный метод который определяет есть ли у метода описание request\response модели
        и если есть то возвращает описание этих моделей в виде списка словарей

        :param data: Кортеж в формате (тип метода, название метода)
        :return: Список кортежей с request и response моделями
        """

        method = data["method"]
        end_point = data["end_point"]

        result = []
        requestBody = self.swagger_dict['paths'][end_point][method].get('requestBody')
        responseBody = self.swagger_dict['paths'][end_point][method].get('responses')
        if requestBody:
            if requestBody['content'].get('application/json'):
                request_model_name = requestBody['content']['application/json']['schema']['$ref'].split('/')[-1]
            elif requestBody['content']['multipart/form-data']['schema'].get('$ref'):
                request_model_name = requestBody['content']['multipart/form-data']['schema']['$ref'].split('/')[
                    -1]
            elif requestBody['content']['multipart/form-data']['schema']['properties']['name'].get('$ref'):
                request_model_name = \
                    requestBody['content']['multipart/form-data']['schema']['properties']['name']['$ref'].split(
                        '/')[-1]

            result.append(
                (self.swagger_dict['components']['schemas'][request_model_name]['properties'],
                 request_model_name)
            )
        if responseBody:
            status_code = self.status_code(data)
            if responseBody[status_code].get('content'):
                response_name_model = \
                    responseBody[status_code]['content']['application/json']['schema']['$ref'].split('/')[-1]
                result.append(
                    (self.swagger_dict['components']['schemas'][response_name_model]['properties'],
                     response_name_model)
                )
        return result

    def _method_model_v2(self, dictionary, model_name):
        """
        Вспомогательный метод который раскрывает и формирует request\response модель данных

        :param dictionary: Json(Словарь) в котором лежит опиание модели
        :param model_name: Название модели в которой лежит описание
        :return: описание request\response модели данных метода
        """
        d = 'class ' + model_name + '(Model):\n'
        global temp
        if isinstance(dictionary, dict):
            for k, v in dictionary.items():
                check_key = v.get('type')
                if check_key == 'number' or check_key == 'integer':
                    d += f'\t{k} = IntField()\n'
                elif check_key == 'array':
                    if v.get('$ref'):
                        model = v['$ref'].split('/')[-1]
                        d += f'\t{k} = ListField({model})\n'
                        dd.setdefault(model, v['$ref'])
                    elif v['items'].get('$ref'):
                        model = v['items']['$ref'].split('/')[-1]
                        if self.swagger_dict['components']['schemas'][model].get('enum'):
                            d += f'\t{k} = ListField()\n'
                        elif self.swagger_dict['components']['schemas'].get(model):
                            if model not in temp:
                                d += f'\t{k} = ListField({model})\n'
                                dd.setdefault(model, v['items']['$ref'])
                            else:
                                d += f'\t{k} = ListField()\n'

                    elif v['items'].get('type'):
                        d += f'\t{k} = ListField()\n'
                elif check_key == 'boolean':
                    d += f'\t{k} = BoolField()\n'
                elif check_key == 'string':
                    d += f'\t{k} = StringField()\n'
                elif not check_key:
                    if v.get('$ref'):
                        model = v['$ref'].split('/')[-1]
                        if self.swagger_dict['components']['schemas'][model].get('enum'):
                            d += f'\t{k} = StringField()\n'
                        else:
                            d += f'\t{k} = EmbeddedField({model})\n'
                            dd.setdefault(model, v['$ref'])

        results.append(d)

        try:
            for k, v in dd.items():
                temp = k
                dd.pop(k)
                self._method_model_v2(self.swagger_dict['components']['schemas'][temp]['properties'], temp)

        except RuntimeError:
            pass

        return results

    def _request_json_parameters(self, data):
        """
        Вспомогательный метод который из request модели собирает список параметров, при этом переименовывая
        переменные, чтобы была понятна структура вложенности и избавлясь от родительских переменных

        :param data: Кортеж в формате (тип метода, название метода)
        :return: Набор параметров которые описаны в request модели метода
        """
        res = []
        for v1, v2 in self._model_dict_v2(data):
            m = self._method_model_v2(v1, v2)
            if 'Response' not in str(m):
                for i in m:
                    match1 = re.search(r'class .*Request\(Model\):?', i)
                    match2 = re.search(r'class .*\(Model\):?', i)
                    if match1:
                        i = i.replace(match1.group(), '')
                        for j in i.split('\n'):
                            if 'EmbeddedField' not in j:
                                value = j.split('=')[0].strip()
                                if value != '':
                                    res.append(value)
                    elif 'Request' not in match2.group():
                        service_name = self.service_name()
                        temp_value = re.sub(f'({service_name})|(class )|(Model)|([():])', '', match2.group())
                        i = i.replace(match2.group(), '')
                        for j in i.split('\n'):
                            if 'EmbeddedField' not in j:
                                value = j.split('=')[0].strip()
                                if value != '':
                                    res.append(temp_value + value.capitalize())
        global results
        results = []
        return res

    def models(self, data):
        """
        Метод формирует код итоговой request\response модели с импортами и записывает в словарь

        :param data: Кортеж в формате (тип метода, название метода)
        :return: Словарь с request\response моделями
        """
        imports = 'from ozmodel.model import Model\n' + \
                  'from jsonmodels.fields import StringField, IntField, ListField, EmbeddedField, BoolField\n\n\n'
        global results
        res = {}
        for v1, v2 in self._model_dict_v2(data):
            m = self._method_model_v2(v1, v2)
            if 'Response' in str(m):
                res['Response'] = imports + '\n\n'.join(reversed(m))
            elif 'Request' in str(m):
                res['Request'] = imports + '\n\n'.join(reversed(m))
            results = []
        return res

    def write_models(self, data, m):
        path = Path(self.folder).joinpath('models', self.service_name().lower())

        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)

        if m:
            with open(f'{path}/{self.name(data)}_request_model.py', 'w') as f:
                f.write(m)

    def request_model(self, data):
        r = str(self._model_dict(data))
        count = 0
        while True:
            for i in self.get_all_models():
                for k, v in i.items():
                    if k in r:
                        r = r.replace(f"'{k}'", str(v))
            # TODO вот тут тоже, так себе проверочка
            if count == 100:
                return literal_eval(r)
            count += 1

    def get_all_models(self):
        results = []
        try:
            for k, v in self.swagger_dict['components']['schemas'].items():
                if v.get('properties'):
                    temp = {}
                    for i, j in v['properties'].items():
                        type_value = j.get('type')
                        if type_value == 'array':
                            if j['items'].get('$ref'):
                                temp[i] = [j['items']['$ref'].split('/')[-1]]
                            else:
                                temp[i] = [j['items']['type']]
                        elif type_value == 'object':
                            try:
                                temp[i] = j['$ref'].split('/')[-1]
                            except KeyError:
                                temp[i] = j['additionalProperties']['$ref'].split('/')[-1]
                        elif type_value is None:
                            temp[i] = j['$ref'].split('/')[-1]
                        else:
                            temp[i] = type_value
                    results.append({k: temp})
            return results
        except KeyError:  # TODO тут надо подумать не все модели парсятся
            return []

    def _check_request_body(self, data):
        method = data["method"]
        end_point = data["end_point"]
        return self.swagger_dict['paths'][end_point][method].get('requestBody')

    @staticmethod
    def name(data, check_tag=False):
        tag = data["tag"].lower()
        end_point = data["end_point"]
        end_point = re.sub(r'\B([A-Z])|(-)|(/)', r'_\1', re.sub(r'[ {}]', '', end_point)).lower()[1:]
        if check_tag:
            end_point = re.sub(f'^{tag}_', '', end_point)
        return end_point

    def code_of_method(self, data):
        service_name = self.service_name().lower()
        data = self._check_input(data)
        parameters = self.parameters(data)
        description = self.description(data)
        json_request = self._check_request_body(data)
        method_name = self.name(data, check_tag=True)
        tag = data["tag"]
        method = data["method"]
        end_point = data["end_point"]
        params = parameters.get('query') if parameters else None
        headers = parameters.get('header') if parameters else None
        path_parameters = parameters.get('path') if parameters else None
        if path_parameters:
            path_parameters = {k: f'{{data["path"]["{k}"]}}' for k, v in parameters.get('path').items()}

        if any([params, json_request, headers]) and path_parameters:
            code = f"""
        @step('{description}')
        def {method}_{method_name}(self, data: dict) -> Response:
            end_point = f'{end_point}'
            return self.app.{service_name}_api.{method}(end_point, **data["request"])""".format(
                **path_parameters)
        elif any([params, json_request, headers]) and not path_parameters:
            code = f"""
        @step('{description}')
        def {method}_{method_name}(self, data: dict) -> Response:
            end_point = f'{end_point}'
            return self.app.{service_name}_api.{method}(end_point, **data["request"])"""
        elif params == json_request == headers == path_parameters is None:
            code = f"""
        @step('{description}')
        def {method}_{method_name}(self) -> Response:
            end_point = f'{end_point}'
            return self.app.{service_name}_api.{method}(end_point)"""
        elif params == json_request == headers is None and path_parameters:
            code = f"""
        @step('{description}')
        def {method}_{method_name}(self, data: dict) -> Response:
            end_point = f'{end_point}'
            return self.app.{service_name}_api.{method}(end_point)""".format(**path_parameters)
        else:
            raise AssertionError(f'Не обработанный случай, {data}, {params}, {path_parameters}, {json_request}')

        return tag, code

    def code_of_test_method(self, data):
        data = self._check_input(data)
        """
        Метод формирует строку с готовым кодом теста

        :param data: Кортеж в формате (тип метода, название метода)
        :return: Строка с готовым кодом теста
        """
        method = data["method"]
        description = self.description(data)
        method_name = self.name(data, check_tag=True)
        service = self.service_name().lower()
        subclass = re.sub(r'\B([A-Z])', r'_\1', data["tag"]).lower()
        test = f'''@allure.story('{description}')
def test_{subclass}_{method}_{method_name}(app, data_{subclass}_{method}_{method_name}):
    data = data_{subclass}_{method}_{method_name}
    response = app.{service}.{subclass}.{method}_{method_name}(data)
    assert response.status_code == data["expected"]["status_code"]
        
        '''
        return test + '\n'

    def _init_all_classes_in_methods(self):
        result = []
        s = f"""# -*- coding: windows-1251 -*-
from requests.models import Response
from ozlogger.step_wrapper import step


class {self.service_name()}:
    def __init__(self, app):\n"""
        result.append(s)
        for mtd in self.methods():
            subclass = re.sub(r'\B([A-Z])', r'_\1', mtd["tag"]).lower()
            i = f'        self.{subclass} = self._{mtd["tag"]}(app)\n'
            if i not in result:
                result.append(i)
        return result

    def _all_methods_code(self):
        results = {}
        for mtd in self.methods():
            results.setdefault(mtd["tag"], [])
            tag, code = self.code_of_method(mtd)
            s = f"""
    class _{tag}:
        def __init__(self, app):
            self.app = app\n"""
            if tag in results:
                if s not in results[tag]:
                    results[tag].append(s)
                results[tag].append(code + '\n')

        return results

    def write_all_methods_layer(self):
        service_name = self.service_name().lower()
        base_path = Path(self.folder).joinpath('services')
        base_path.mkdir(parents=True, exist_ok=True)
        with open(base_path.joinpath(f'{service_name}.py'), 'w') as methods_layer:
            for _ in self._init_all_classes_in_methods():
                methods_layer.write(_)
            for _ in self._all_methods_code().values():
                for __ in _:
                    methods_layer.write(__)

    def write_all_tests_layer(self):
        service_name = self.service_name().lower()
        base_path = Path(self.folder).joinpath('tests')
        base_path.mkdir(parents=True, exist_ok=True)
        with open(base_path.joinpath(f'test_{service_name}.py'), 'w') as tests_layer:
            tests_layer.write('import allure\n\n\n')
            for _ in self.methods():
                tests_layer.write(self.code_of_test_method(_))

    def create_test_data(self, data):
        data = self._check_input(data)
        method = data["method"]
        parameters = self.parameters(data)
        method_name = self.name(data, check_tag=True)
        json_request = self.request_model(data)
        params = parameters.get('query') if parameters else None
        headers = parameters.get('header') if parameters else None
        path_parameters = parameters.get('path') if parameters else None

        td = {
            'test_name': f'test {method}_{method_name}',
            'expected': {
                'status_code': int(self.status_code(data))
            }
        }
        if any([params, headers, json_request]):
            td['request'] = {}
        if params:
            td['request']['params'] = params
        if headers:
            td['request']['headers'] = headers
        if self._check_request_body(data):
            if json_request.get('type') == 'object':
                td['request']['data'] = ['files']
            else:
                td['request']['json'] = json_request
        if path_parameters:
            td['path'] = path_parameters
        return td

    def write_test_data(self, data):
        data = self._check_input(data)
        method = data["method"]
        subclass = re.sub(r'\B([A-Z])', r'_\1', data["tag"]).lower()
        service_name = self.service_name().lower()
        method_name = self.name(data, check_tag=True)
        base_path = Path(self.folder).joinpath('data', service_name)
        base_path.mkdir(parents=True, exist_ok=True)
        file = f'{base_path}/{subclass}_{method}_{method_name}.py'
        if not Path(file).is_file():
            with open(file, 'w') as f:
                f.write(f'test_data = {json.dumps([self.create_test_data(data)], indent=4)}')
        else:
            print(f'Файл {file} уже существует')

    def create_app_fixture(self, write=False):
        service_name = self.service_name()
        app_sting = f'''from ozrestclient.restclient import RestClient
from services.{service_name.lower()} import {service_name}
        
        
class Application:
    def __init__(self, base_url=None, headers=None):
        self.{service_name.lower()} = {service_name}(self)
        self.base_url = base_url
        self.{service_name.lower()}_api = RestClient(host=base_url, headers=headers)
        '''
        if write:
            base_path = Path(self.folder).joinpath('fixture')
            base_path.mkdir(parents=True, exist_ok=True)
            file = base_path.joinpath('application.py')
            if not file.is_file():
                with open(file, 'w') as f:
                    f.write(app_sting)
        return app_sting

    def create_folders(self):
        service_name = self.service_name().lower()
        Path(self.folder).joinpath('fixture').mkdir(parents=True, exist_ok=True)
        Path(self.folder).joinpath(f'services').mkdir(parents=True, exist_ok=True)
        Path(self.folder).joinpath(f'data/{service_name}').mkdir(parents=True, exist_ok=True)
        Path(self.folder).joinpath('tests').mkdir(parents=True, exist_ok=True)

    def add_code_of_method(self, data):
        try:
            tag, code = self.code_of_method(data)
            path = Path(self.folder).joinpath('services', f'{self.service_name().lower()}.py')
            if not path.is_file():
                self.create_app_fixture(write=True)
                with open(path, 'w') as methods_layer:
                    for _ in self._init_all_classes_in_methods():
                        methods_layer.write(_)

                    results = {}
                    for mtd in self.methods():
                        results.setdefault(mtd["tag"], [])
                        tag1, code1 = self.code_of_method(mtd)
                        s = f"""
    class _{tag1}:
        def __init__(self, app):
            self.app = app\n"""

                        if tag1 in results:
                            if s not in results[tag1]:
                                results[tag1].append(s)

                    for _ in results.values():
                        for __ in _:
                            methods_layer.write(__)


            file = open(path).readlines()

            try:
                index = list(map(str.lower, file)).index(f'    class _{tag.lower()}:\n') + 3
                for i in code.split('\n'):
                    file.insert(index, i + '\n')
                    index = index + 1

            except ValueError:
                print(f"При добавлении метода {data}\nв класс {tag} произошла ошибка, код мог быть сгенерирован не корректно")
                with open(path, 'a') as f:
                    f.write('\n"""\nНе был найден нужный подкласс код данного метода был сгенерирован без привязки к подклассу\n')
                    f.write(code)
                    f.write('\n"""\n\n ')

            with open(path, 'r') as f:
                if code.strip() in f.read():
                    print('Код данного метода уже существует!')
                    return

            with open(path, 'w') as f:
                for i in file:
                    f.write(i)

        except BaseException as error:
            print(f"В методе add_code_of_method произошла ошибка '{error}'!!! код мог быть сгенерирован не корректно")
