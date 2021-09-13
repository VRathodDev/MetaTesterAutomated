import random
import winreg
import platform
import re
import os

from GenUtility import TimeOutLevel, isNoneOrEmpty, runExecutable, writeInFile
from Input import InputReader
from RemoteConnection import RemoteConnection
from MetaTestRunner import MetaTester
from getpass import getpass


class INIFileTester:

    @staticmethod
    def run(inDSN: str, inDriverBit: int, inLogsPath: str, inDriverRegistryConfig: dict,
            inWaitForUserToSetupDSN: bool = False):
        """
        Tests if error-messages are correctly accessed using INI File \n
        :param inWaitForUserToSetupDSN: If True Wait for user to modify DSN Setup
        :param inDSN: Name of the Data Source
        :param inDriverBit: Bit count of Driver
        :param inLogsPath: Path to save logs
        :param inDriverRegistryConfig: Registry Configurations in Key Value pair
        :return: True if succeeded else False
        """
        if not isNoneOrEmpty(inDSN, inLogsPath):
            incorrectDSNConfig = dict()
            correctDSNConfig = dict()
            hadFailure = False
            if inWaitForUserToSetupDSN:
                print('Instruction: Set one of the Connection Property `wrong` such that '
                      'Driver would show an Error Message')
                runExecutable('odbcad32.exe', TimeOutLevel.MEDIUM)
            else:
                for key, value in inDriverRegistryConfig.items():
                    if key.lower() == 'host':
                        incorrectDSNConfig = {'Host': ''.join(random.sample(list(value), len(value)))}
                        correctDSNConfig = {'Host': value}
                        break
                else:
                    incorrectDSNConfig = {'UseEncryptedEndpoints': '0'}
                    correctDSNConfig = {'UseEncryptedEndpoints': '1'}
                if not INIFileTester._setupDriverConfigurationsInRegistry(inDSN, inDriverBit, incorrectDSNConfig):
                    return False
            try:
                logs = MetaTester.run(inDSN, inDriverBit)
                writeInFile(logs, inLogsPath)
                hadFailure = not INIFileTester._parseLogs(logs)
            except Exception as error:
                print(f"Error: {error}")
                hadFailure = True
            finally:
                if inWaitForUserToSetupDSN:
                    print('Instruction: Set the Connection Properties to its correct values!')
                    runExecutable('odbcad32.exe')
                else:
                    if len(correctDSNConfig) > 0:
                        INIFileTester._setupDriverConfigurationsInRegistry(inDSN, inDriverBit, correctDSNConfig)
                    else:
                        INIFileTester._setupDriverConfigurationsInRegistry(inDSN, inDriverBit, inDriverRegistryConfig)
                return not hadFailure
        else:
            print('Error: Invalid Arguments passed')
            return False

    @staticmethod
    def _setupDriverConfigurationsInRegistry(inTargetKey: str, inDriverBit: int, inDriverRegistryConfig: dict):
        """
        Sets required Driver Configurations on the `determined` registry path \n
        :param inTargetKey: Name of the registry key to create or modify values
        :param inDriverBit: Driver's Bit Count
        :param inDriverRegistryConfig: Registry Configurations in Key Value pair
        :return: True if succeeded else False
        """
        if inDriverBit is not None and inDriverBit in [32, 64] and (not isNoneOrEmpty(inDriverRegistryConfig)):
            systemBit = int(platform.architecture()[0][:2])
            try:
                with winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE) as hkey:
                    with winreg.OpenKey(hkey, 'Software', 0, winreg.KEY_WRITE) as parentKey:
                        if systemBit != inDriverBit:
                            parentKey = winreg.OpenKey(parentKey, 'Wow6432Node', 0, winreg.KEY_WRITE)
                        with winreg.OpenKey(parentKey, 'ODBC', 0, winreg.KEY_WRITE) as odbcKey:
                            with winreg.OpenKey(odbcKey, 'ODBC.INI', 0, winreg.KEY_WRITE) as odbcIniKey:
                                with winreg.CreateKeyEx(odbcIniKey, inTargetKey, 0, winreg.KEY_ALL_ACCESS) as driverKey:
                                    for key, value in inDriverRegistryConfig.items():
                                        winreg.SetValueEx(driverKey, key, 0, winreg.REG_SZ, value)
            except Exception as e:
                print(f"Error: {e}")
                return False
            return True
        else:
            print('Error: Invalid Arguments passed')
            return False

    @staticmethod
    def _parseLogs(inLogs: str):
        """
        Parses the MetaTester generated Logs for `INI` File Test \n
        :param inLogs: `MetaTester` generated Logs
        :return: True if succeeded else False
        """
        if not isNoneOrEmpty(inLogs):
            if 'An error occurred while attempting to retrieve the error message for key' not in inLogs:
                for currLine in inLogs.splitlines():
                    if '*** ODBC Error/Warning:' in currLine:
                        matchedStr = re.match(r'\*\*\* ODBC Error/Warning: \[([A-Z0-9]+)\] '
                                              r'\[([A-Za-z0-9]+)\]\[([A-Za-z0-9]+)\]'
                                              r' \(([0-9]+)\) (.)', currLine)
                        if len(matchedStr.groups()) >= 5:
                            print(f"Expected ErrorMessage for INI File Test found: {currLine}")
                            return True
                return False
            else:
                return False
        else:
            print('Error: Empty Content passed to parse')
            return False


def main(inUserName: str, inPassword: str, inputFileName: str):
    userName = inUserName
    password = inPassword
    inputReader = InputReader(inputFileName)
    summary = dict()
    remoteConnection = RemoteConnection(inputReader.getRemoteMachineAddress(), userName, password)
    if remoteConnection.connect():
        coreInfo = inputReader.getCoreInfo()
        if coreInfo.download():
            summary['CoreSetup'] = 'Succeed'
        else:
            summary['CoreSetup'] = 'Failed'
            return summary

        summary['Plugins'] = dict()
        for pluginInfo in inputReader.getPluginInfo():
            sourceFilePath = os.path.abspath(pluginInfo.getSourcePath())

            if pluginInfo.setup(coreInfo):
                summary['Plugins'][sourceFilePath] = dict()
                summary['Plugins'][sourceFilePath]['Setup'] = 'Succeed'
                logsPath = os.path.join(pluginInfo.getLogsPath(), f"{pluginInfo.getPluginBrand()}_"
                                                                  f"{pluginInfo.getPackageName()}_"
                                                                  f"INIFileTestLogs.txt")
                MetaTesterPath = os.path.abspath('MetaTester')
                if not os.path.exists(MetaTesterPath):
                    MetaTesterPath = None
                if INIFileTester.run(pluginInfo.getDataSourceName(), pluginInfo.getPackageBitCount(), logsPath,
                                     pluginInfo.getDataSourceConfiguration(),
                                     pluginInfo.shouldWaitForUserToSetupDSN()):
                    summary['Plugins'][sourceFilePath]['INIFileTest'] = 'Succeed'
                    summary['Plugins'][sourceFilePath]['INIFileTestLogs'] = logsPath
                    print(f"{sourceFilePath}: INI File Test ran to completion successfully")
                else:
                    summary['Plugins'][sourceFilePath]['MetaDataTest'] = 'Failed'
                    summary['Plugins'][sourceFilePath]['MetaDataTestLogs'] = logsPath
                    print(f"{sourceFilePath}: INI File Test failed")
            else:
                summary['Plugins'][sourceFilePath] = 'Failed'
        remoteConnection.disconnect()
        return summary


if __name__ == '__main__':
    main(input(), getpass(), 'input.json')
