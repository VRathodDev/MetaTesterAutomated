# import os
# import platform
# import random
# import subprocess
# import sys
# import uuid
import json
import os
import sys
import winreg
# from collections import OrderedDict
# from Runner import INIFileTester
# # print(INIFileTester._setupDriverConfigurationsInRegistry('Microsoft Hubspot', 64, {'HOST': 'TestMe'}))
# # if __name__ == '__main__':
# #     pass
# regValues = OrderedDict()
# with winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE) as hkey:
#     with winreg.OpenKey(hkey, 'Software', 0, winreg.KEY_WRITE) as softwareKey:
#         with winreg.OpenKey(softwareKey, 'ODBC', 0, winreg.KEY_WRITE) as odbcKey:
#             with winreg.OpenKey(odbcKey, 'ODBC.INI', 0, winreg.KEY_WRITE) as odbcInstIniKey:
#                 with winreg.CreateKeyEx(odbcInstIniKey, 'Microsoft Hubspot', 0, winreg.KEY_ALL_ACCESS) as driverKey:
#                     keyIndex = 0
#                     while keyIndex >= 0:
#                         try:
#                             if winreg.EnumValue(driverKey, keyIndex)[1] != '':
#                                 regValues[winreg.EnumValue(driverKey, keyIndex)[0]] = winreg.EnumValue(driverKey, keyIndex)[1]
#                             keyIndex += 1
#                         except Exception:
#                             for key, value in regValues.items():
#                                 print(f"\"{key}\": \"{value}\",")
#                             break
# # with winreg.OpenKey(odbcInstIniKey, 'IBM Facebook ODBC Driver', 0, winreg.KEY_ALL_ACCESS) as facebookKey:
# #     print(winreg.QueryValueEx(facebookKey, 'Setup'))
# # winreg.SetValueEx(facebookKey, 'ProxyHost', 0, winreg.REG_SZ, 'localhost')
# # winreg.DeleteKeyEx(odbcInstIniKey, 'MR Facebook ODBC Driver', 0, winreg.KEY_ALL_ACCESS)
# #     # systemBit = int(platform.architecture()[0][:2])
# #     # print(systemBit)
#
# # import os
# # print(os.path.exists(None))
# # from Runner import Runner
# # Runner.setupDriverInRegistry(32, "Test", "Driver", "C:/Users/vrathod/PycharmProjects/MetaTesterAutomation/Test.py")
# import re
#
# from Runner import MetaTester
#
# # print(runMetaTester('Microsoft Hubspot', 64, r'C:\Users\vrathod\PycharmProjects\MetaTesterAutomation'))
# # with open('Microsoft_Hubspot_MetaTesterLogs.txt') as file:
# #     print(MetaTester.parseLogs(file.read(), r'C:\Users\vrathod\Desktop\Log.txt'))
# # data = 'Type name mismatch. SQLColumns: BIGINT, SQLGetTypeInfo: UBIGINT'
# data = 'Local type name mismatch. SQLColAttribute: SBIGINT, SQLGetTypeInfo: UBIGINT'
# # ans = re.search('SQLColAttribute: ([a-zA-Z]*), SQLGetTypeInfo: ([a-zA-Z]*),', data)
# # colAttr, typeInfo = ans.groups() if ans is not None else None, None
# # print(colAttr, typeInfo)
# # print(MetaTester._fetchAndCompareSQLType(data, 'BIGINT', 'SQLColAttribute', 'SQLGetTypeInfo'))
# # sys.exit(1)
#
#
# # def dunc(*args):
# #     return all(map(lambda inArgs: inArgs is not None and len(inArgs) > 0, args))
# #
# #
# # print(dunc(None, 'hi', 'Hey', '', ''))
# from Input import Package, Core
# # import os
# # print(os.path.isfile(r'C:\Users\vrathod\Desktop\Test\Hubspot\Hubspot_ODBC_1.6.34.1013_64Bit\DriverLogs\Microsoft_Hubspot_MetaTesterLogs.txt'))
# # print(re.match(r'\*\*\* ODBC Error/Warning: \[([A-Z0-9]+)\] \[([A-Za-z0-9]+)\]\[([A-Za-z0-9]+)\]'
# #                          r' \(([0-9]+)\) ([A-Za-z0-9]+)', '*** ODBC Error/Warning: [HY000] [Microsoft][DriverSupport] '
# #                                                           '(1110) Unexpected response received from server. Please '
# #                                                           'ensure the server host and port specified for the '
# #                                                           'connection are correct and confirm if SSL should be '
# #                                                           'enabled for the connection.').groups())
# # print(''.join(list()))
# # print(random.shuffle(list(data)))
# # print(list(data))
# # print(uuid.uuid3(uuid.NAMESPACE_URL, list(data)))
#
# # out, err = subprocess.Popen(r'C:\Users\vrathod\Perforce\VRathod_1693\SimbaTestTools\ODBC\MetaTester\bin\x64\Debug\MetaTester64.exe -d "Microsoft Hubspot" -o C:\Users\vrathod\Desktop\Test\Test.text', stderr=subprocess.PIPE).communicate()
# # print(out, err)
# # try:
# #     print(subprocess.check_output(r'C:\Users\vrathod\Perforce\VRathod_1693\SimbaTestTools\ODBC\MetaTester\bin\x64\Debug\MetaTester64.exe -d "Microsoft Hubspot" -o C:\Users\vrathod\Desktop\Test\Test.text').stderr)
# # except subprocess.CalledProcessError as e:
# #     out = e.output.decode()
# #
# # print('.')
# # print(out)
#
# # if doNotValidate:
# #     writeInFile(metatesterLogs, inLogsPath)
# #     return True
# import subprocess
#
# subprocess.run(['C:\Windows\System32\cmd.exe', 'C:\Windows\System32\odbcad32.exe'])
import subprocess
import time

# from GenUtility import runExecutable, TimeOutLevel
#
# status = runExecutable('MetaTester.exe')
# print(status)
#
# from Runner import INIFileTester
# with open('Microsoft_Hubspot_MetaTesterLogs.txt') as file:
#     print(INIFileTester.parseLogs(file.read()))
# start_time = time.time()
# process = subprocess.Popen('MetaTester32.exe'
#                  '- d "Microsoft Hubspot" -o C:\\Users\\vrathod\\Desktop\\Hubspot.txt')
# waiting = 3
# while process.poll() is None:
#     if waiting == 0:
#         process.terminate()
#         break
#     waiting -= 1
#     time.sleep(60.0 - ((time.time() - start_time) % 60.0))
# from Packages import Package
# Package('./', './')
# from RemoteConnection import RemoteConnection
# rmc = RemoteConnection('van-wnt-vm.simba.ad', 'Simba\\vipulr', 'Edit321@#')
# print(rmc.connect())
# print(rmc.disconnect())
#
# if __name__ == '__main__':
#     with open('execTest.bat', 'w') as file:
#         file.write(f"cd MetaTester\n")
#         file.write(f"MetaTester64.exe -d \"Microsoft Hubspot\" -o logs.txt")
#
#     print(subprocess.check_output('execTest.bat').decode())
#     os.remove('execTest.bat')
# process = subprocess.Popen('execTest.bat')
# print(process.communicate(timeout=60))
# with open('test.json', 'w') as file:
#     json.dump({'Hey': 'Hi'}, file)
import GenUtility

print(GenUtility.runExecutable('odbcad32.exe'))
