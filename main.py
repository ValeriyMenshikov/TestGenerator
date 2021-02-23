from pathlib import Path
from tkinter import filedialog, Tk
from code_generator import Swagger
import os
import re

if __name__ == '__main__':
    print('Выбери папку куда сохранить проект')
    root = Tk()
    root.withdraw()
    folder_selected = filedialog.askdirectory()
    # os.chdir(folder_selected)
    while True:
        url = str(input('Введи Swagger url:'))
        regex = re.compile(
            r'^(?:http|ftp)s?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        if re.match(regex, url) is not None:
            sw = Swagger(url=url, folder=folder_selected)
            sw.create_env()
            break
        else:
            print('Введен не верный url адрес')

    while True:
        print("""
Чтобы создать на весь сервис введи      '1' 
Чтобы создать на отдельный метод введи  '2' 
Для выхода нажми                        '3' 
        """)
        new = str(input('>'))
        if new in ['1', 1]:
            sw.create_app_fixture(write=True)
            for i in sw.methods():
                print(i)
                sw.write_test_data(i)
                # sw.write_models(i, sw.models(i).get("Request"))
            sw.write_all_tests_layer()
            sw.write_all_methods_layer()
            break
        elif new in ['2', 2]:
            sw.create_folders()
            all_methods_by_type = {}
            for method in sw.methods():
                all_methods_by_type.setdefault(method['method'], [])
                if method['method'] in all_methods_by_type:
                    all_methods_by_type[method['method']].append(method['end_point'])

            while True:
                print('Доступные методы:')
                temp_method_types = dict(enumerate(all_methods_by_type.keys()))
                for num, method_type in temp_method_types.items():
                    print(num, method_type.upper())

                try:
                    selected_method_num = int(input('Какие методы показать?'))
                except ValueError:
                    print('Должно быть целое число и представленного диапазона')
                    continue
                if selected_method_num not in temp_method_types:
                    print('Число должно быть из представленного диапазона')
                else:
                    break

            while True:
                temp_endpoints = dict(enumerate(all_methods_by_type[temp_method_types[selected_method_num]]))
                for num, end_point in temp_endpoints.items():
                    print(num, end_point)

                try:
                    selected_endpoint_num = int(input('Для какого метода создать тест?'))
                except ValueError:
                    print('Должно быть целое число и представленного диапазона')
                    continue
                if selected_endpoint_num not in temp_endpoints:
                    print('Число должно быть из представленного диапазона')
                else:
                    selected_method = temp_method_types[selected_method_num]
                    selected_endpoint = temp_endpoints[selected_endpoint_num]
                    break

            for method in sw.methods():
                if method['method'] == selected_method and method['end_point'] == selected_endpoint:
                    sw.write_test_data(method)
                    # sw.models(method)
                    # sw.write_models(method, sw.models(method).get("Request"))
                    service_name = sw.service_name().lower()
                    test_file = Path(folder_selected).joinpath('tests', f'test_{service_name}.py')
                    if test_file.is_file():
                        test = sw.code_of_test_method(method)
                        with open(test_file, 'r+') as f:
                            if test.strip() in f.read():
                                print('Код для такого теста уже существует')
                            else:
                                if 'import allure' not in f.read():
                                    f.write('import allure\n\n\n')
                                f.write(test)
                    else:
                        with open(test_file, 'w') as f:
                            f.write(sw.code_of_test_method(method))

                    sw.add_code_of_method(method)
        elif new in ['3', 3]:
            exit()
        else:
            print('Введи число из перечисленных.')