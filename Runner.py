import enum
import platform
import random
import re
import winreg
import zipfile

from Input import InputReader
from RemoteConnection import RemoteConnection
from shutil import copy, unpack_archive, copytree
from GenUtility import *
from getpass import getpass


class MetaTester:

    @staticmethod
    def run(inDSN: str, inDriverBit: int):
        """
        Executes `MetaTester` \n
        :param inDSN: Name of the Data Source
        :param inDriverBit: Bit count of Driver
        :return: Returns Generated Logs during MetaTester if successfully completed else None
        """
        if not isNoneOrEmpty(inDSN) and inDriverBit in [32, 64]:
            if 'METATESTER_DIR' in os.environ:
                METATESTER_DIR = os.path.abspath(os.getenv('METATESTER_DIR'))
                if os.path.exists(METATESTER_DIR):
                    MetaTesterPath = os.path.join(METATESTER_DIR, f"MetaTester{inDriverBit}.exe")
                    if os.path.exists(MetaTesterPath):
                        MetaTesterLogFileName = f"{inDSN.replace(' ', '_')}_MetaTesterLogs.txt"
                        command = f"{MetaTesterPath} -d \"{inDSN}\" -o {MetaTesterLogFileName}"
                        try:
                            metatesterLogs = subprocess.check_output(command, timeout=TimeOutLevel.MEDIUM.value).decode()
                            if 'Done validation' in metatesterLogs:
                                return metatesterLogs
                            else:
                                print('Error: MetaTester failed to run to completion successfully')
                                print(f"For more details, "
                                      f"Check logs: {os.path.join(METATESTER_DIR, MetaTesterLogFileName)}")
                                return None

                        except subprocess.CalledProcessError as error:
                            return error.output.decode()

                        except subprocess.TimeoutExpired as error:
                            print(f"Error: \"{command}\" could not be executed in {TimeOutLevel.MEDIUM.value / 60} Minutes!")
                            return None

                        except Exception as error:
                            print(f"Error: {error}")
                            return None
                    else:
                        print(f"Error: MetaTester{inDriverBit}.exe does not exist in {METATESTER_DIR}")
                        return None
                else:
                    print(f"Error: Invalid Path {METATESTER_DIR} set for Environment Variable `METATESTER_DIR`")
                    return None
            else:
                print('Error: Environment Variable `METATESTER_DIR` does not exist')
                return None
        else:
            print('Error: Invalid Parameters')
            return None

    @staticmethod
    def parseLogs(inLogs: str, inParsedLogsPath: str):
        """
        Parses the `MetaTester` generated Logs\n
        :param inLogs: `MetaTester` generated Logs
        :param inParsedLogsPath: Path to save the parsed Logs including the Log File Name
        :return: True if succeeded else False
        """
        if not isNoneOrEmpty(inLogs, inParsedLogsPath):
            if not inParsedLogsPath.endswith('.txt'):
                print(f"Error: {inParsedLogsPath} must contain Log File Name with `.txt` File Extension. "
                      f"i.e `Z:fakepath/log_file.txt")
                return False
            startChecking = False
            parsedLogs = ''
            columnType = ''
            hadFailure = False
            totalFailures = 0
            for currLine in inLogs.splitlines():
                if 'Validating individual columns...' == currLine:
                    hadFailure = False
                    startChecking = True
                elif 'Done validating individual columns.' == currLine:
                    totalFailures += 1 if hadFailure else 0
                    startChecking = False
                elif startChecking:
                    if currLine != 'Verifying SQLPreare':
                        if 'Column:' in currLine:
                            ans = re.search('Type Name: ([a-zA-Z]*)', currLine)
                            columnType = ans.groups()[0] if ans is not None else None
                        elif 'Type name mismatch' in currLine or 'Local type name mismatch' in currLine:
                            status = None
                            if 'SQLColumns' in currLine and 'SQLGetTypeInfo' in currLine:
                                status = not MetaTester._fetchAndCompareSQLType(currLine, columnType,
                                                                                'SQLColumns', 'SQLGetTypeInfo')
                                currLine += ' --- Critical' if status else ' --- Checked'
                            elif 'SQLColAttribute' in currLine and 'SQLGetTypeInfo' in currLine:
                                status = not MetaTester._fetchAndCompareSQLType(currLine, columnType,
                                                                                'SQLColAttribute', 'SQLGetTypeInfo')
                                currLine += ' --- Critical' if status else ' --- Checked'
                            if status:
                                hadFailure = True
                        elif 'Unsigned mismatch' in currLine:
                            currLine += ' --- Checked'
                        else:
                            currLine += ' --- Critical'
                            hadFailure = True
                else:
                    if 'Number of table failures' in currLine:
                        currLine = f"Number of table failures: {totalFailures}\n"
                parsedLogs += currLine + '\n'

            writeInFile(parsedLogs, inParsedLogsPath)
            return not hadFailure
        else:
            print('Error: Invalid Parameter')
            return False

    @staticmethod
    def _fetchAndCompareSQLType(inData: str, inTargetKey: str, *inTargetAttributes: str):
        """
        Extracts the SQLType from given data using given attributes and matches with the Target Key\n
        :param inData: A String containing the attributes and associated values
        :param inTargetKey: Key to compare with associated values of the given attributes
        :param inTargetAttributes: Attributes within the given Data
        :return: True if TargetKey matches all of the attributes' associated values else False
        """
        if not isNoneOrEmpty(inData, inTargetKey, *inTargetAttributes):
            for attr in inTargetAttributes:
                regexPattern = re.search(f"{attr}: ([a-zA-Z]*)", inData)
                if regexPattern is not None:
                    if inTargetKey not in regexPattern.groups()[0]:
                        return False
                else:
                    return False
            return True
        else:
            print('Error: Invalid Parameter')
            return False


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
                                              r' \(([0-9]+)\) ([A-Za-z0-9]+)', currLine)
                        if len(matchedStr.groups()) >= 5:
                            print(f"Expected ErrorMessage for INI File Test found: {currLine}")
                            return True
                return False
            else:
                return False
        else:
            print('Error: Empty Content passed to parse')
            return False


class Runner:
    def __init__(self, inUserName: str, inPassword: str, inputFileName: str):
        self.mUserName = inUserName
        self.mPassword = inPassword
        self.mInput = InputReader(inputFileName)

    def run(self):
        summary = dict()
        remoteConnection = RemoteConnection(self.mInput.getRemoteMachineAddress(), self.mUserName, self.mPassword)
        if remoteConnection.connect():
            coreInfo = self.mInput.getCoreInfo()
            if copyFile(coreInfo.getSourcePath(), coreInfo.getDestinationPath(),
                        coreInfo.getFileName(), coreInfo.shouldForceUpdate()):
                unpack_archive(os.path.join(coreInfo.getDestinationPath(), coreInfo.getSourcePath().split(os.sep)[-1]),
                               coreInfo.getDestinationPath())
                summary['CoreSetup'] = 'Succeed'
            else:
                summary['CoreSetup'] = 'Failed'
                return summary

            summary['Plugins'] = dict()
            for pluginInfo in self.mInput.getPluginInfo():
                sourceFilePath = os.path.abspath(pluginInfo.getSourcePath())
                destinationFolderPath = os.path.abspath(pluginInfo.getDestinationPath())
                fileName = pluginInfo.getFileName()

                if not copyFile(sourceFilePath, destinationFolderPath, fileName, pluginInfo.shouldForceUpdate()):
                    summary['Plugins'][sourceFilePath] = 'Failed'
                    break
                if os.path.isfile(sourceFilePath) and zipfile.is_zipfile(sourceFilePath):
                    dataSourceName, fileBitness = pluginInfo.getDataSourceName(), pluginInfo.getPackageBitCount()

                    unpack_archive(os.path.join(destinationFolderPath, fileName), destinationFolderPath)

                    if Runner.setupDriverPackage(coreInfo, pluginInfo):
                        summary['Plugins'][sourceFilePath] = dict()
                        summary['Plugins'][sourceFilePath]['Setup'] = 'Succeed'
                        if pluginInfo.shouldWaitForUserToSetupDSN():
                            print(f"Provide Required Configurations for {dataSourceName} DSN")
                            runExecutable('odbcad32.exe')
                        driversLogsPath = os.path.abspath(os.path.join(destinationFolderPath, 'DriverLogs'))
                        logsPath = os.path.join(driversLogsPath, f"{pluginInfo.getPluginBrand()}_"
                                                                 f"{pluginInfo.getPackageName()}_MetaTesterLogs.txt")
                        metaTesterLogs = MetaTester.run(dataSourceName, fileBitness)
                        if MetaTester.parseLogs(metaTesterLogs, logsPath):
                            summary['Plugins'][sourceFilePath]['MetaDataTest'] = 'Succeed'
                            summary['Plugins'][sourceFilePath]['MetaDataTestLogs'] = logsPath
                            print(f"{sourceFilePath}: MetaTester ran to completion successfully")
                        else:
                            summary['Plugins'][sourceFilePath]['MetaDataTest'] = 'Failed'
                            summary['Plugins'][sourceFilePath]['MetaDataTestLogs'] = logsPath
                            print(f"{sourceFilePath}: MetaTester reported critical errors")

                        logsPath = os.path.join(driversLogsPath, f"{pluginInfo.getPluginBrand()}_"
                                                                 f"{pluginInfo.getPackageName()}_INIFileTestLogs.txt")
                        if INIFileTester.run(dataSourceName, fileBitness, logsPath,
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
                    print('Error: Invalid Source Path provided.\nExpected File Extension is .Zip')
                    summary['Plugins'][sourceFilePath] = 'Failed'
            remoteConnection.disconnect()
        return summary

    @staticmethod
    def setupDriverPackage(inCoreInfo: InputReader.Core, inPluginInfo: InputReader.Plugin):
        brand = inPluginInfo.getPluginBrand()
        extractedPluginPath = inPluginInfo.getDestinationPath()
        driverName = inPluginInfo.getPackageName()

        coreBranch = inCoreInfo.getBranch()
        extractedCorePath = inCoreInfo.getDestinationPath()
        pluginLibFolderPath = os.path.join(extractedPluginPath, 'lib')
        if not os.path.exists(os.path.join(extractedPluginPath, f"Branding\\{brand}")):
            if os.path.exists(os.path.join(extractedPluginPath, f"Branding\\Simba")):
                brand = 'Simba'
            else:
                print('Error: ' + os.path.join(extractedPluginPath, f"Branding\\Simba") + ' and ' +
                      os.path.join(extractedPluginPath, f"Branding\\{brand}") + ' not found')
                return False
        pluginDIDPath = os.path.join(extractedPluginPath, f"Branding\\{brand}\\{driverName}ODBC.did")
        pluginINIPath = os.path.join(extractedPluginPath, f"lib\\CoreBranding\\Simba\\Setup\\rdf.rdfodbc.ini")
        coreLibPath = os.path.join(extractedCorePath, f"Core\\{coreBranch}\\ODBC\\lib")
        coreThirdPartyPath = os.path.join(extractedCorePath, f"Core\\{coreBranch}\\ODBC\\ThirdParty")
        pluginINIFileInLib = os.path.join(pluginLibFolderPath, f"{brand}.{driverName}ODBC.ini")

        if all(map(lambda filePath: os.path.exists(filePath),
                   [pluginDIDPath, pluginINIPath, coreLibPath, coreThirdPartyPath])):
            copy(pluginDIDPath, pluginLibFolderPath)
            copy(pluginINIPath, pluginINIFileInLib)
            copytree(coreLibPath, pluginLibFolderPath, dirs_exist_ok=True)
            copytree(coreThirdPartyPath, pluginLibFolderPath, dirs_exist_ok=True)

            with open(pluginINIFileInLib, 'a') as file:
                file.write('\n')
                file.write(f"ErrorMessagesPath={os.path.join(extractedPluginPath, 'ErrorMessages')}\n")

            return Runner.setupDriverInRegistry(inPluginInfo.getPackageBitCount(), inPluginInfo.getDataSourceName(),
                                                os.path.join(pluginLibFolderPath, 'MPAPlugin.dll'),
                                                inPluginInfo.getDataSourceConfiguration(),
                                                inPluginInfo.shouldWaitForUserToSetupDSN())
        else:
            print('Error: Core or Plugin is not correctly extracted')
            return False

    @staticmethod
    def setupDriverInRegistry(inDriverBit: int, inDataSourceName: str, inDriverDLLPath: str,
                              inDriverRegistryConfig: dict, inWaitForUserToSetupDSN: bool = False):
        """
        Sets Driver DLL Path at appropriate Node in the registry\n
        :return: True if succeeded else False
        """
        if not isNoneOrEmpty(inDataSourceName, inDriverDLLPath):
            if inDriverBit in [32, 64]:
                systemBit = int(platform.architecture()[0][:2])
                if systemBit < inDriverBit:
                    print(f"Error: Registry Configurations can not be altered for "
                          f"{inDriverBit}Bit Driver on {systemBit}Bit OS")
                    return False
                elif inDriverDLLPath is None or not os.path.exists(inDriverDLLPath):
                    print('Error: Invalid Driver DLL Path provided')
                    return False
                else:
                    with winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE) as hkey:
                        with winreg.OpenKey(hkey, 'Software', 0, winreg.KEY_WRITE) as parentKey:
                            if systemBit != inDriverBit:
                                parentKey = winreg.OpenKey(parentKey, 'Wow6432Node', 0, winreg.KEY_WRITE)
                            with winreg.OpenKey(parentKey, 'ODBC', 0, winreg.KEY_WRITE) as odbcKey:
                                with winreg.OpenKey(odbcKey, 'ODBCINST.INI', 0, winreg.KEY_WRITE) as odbcInstIniKey:
                                    with winreg.CreateKeyEx(odbcInstIniKey, f"{inDataSourceName} ODBC Driver",
                                                            0, winreg.KEY_ALL_ACCESS) as driverKey:
                                        winreg.SetValueEx(driverKey, 'Description', 0, winreg.REG_SZ,
                                                          f"{inDataSourceName} ODBC Driver")
                                        winreg.SetValueEx(driverKey, 'Driver', 0, winreg.REG_SZ, inDriverDLLPath)
                                        winreg.SetValueEx(driverKey, 'Setup', 0, winreg.REG_SZ, inDriverDLLPath)

                                    with winreg.CreateKeyEx(odbcInstIniKey, 'ODBC Drivers', 0,
                                                            winreg.KEY_ALL_ACCESS) as odbcDriversKey:
                                        winreg.SetValueEx(odbcDriversKey, f"{inDataSourceName} ODBC Driver",
                                                          0, winreg.REG_SZ, 'Installed')

                                with winreg.OpenKey(odbcKey, 'ODBC.INI', 0, winreg.KEY_WRITE) as odbcIniKey:
                                    with winreg.OpenKey(odbcIniKey, 'ODBC Data Sources', 0,
                                                        winreg.KEY_WRITE) as odbcDSkey:
                                        winreg.SetValueEx(odbcDSkey, f"{inDataSourceName}",
                                                          0, winreg.REG_SZ, f"{inDataSourceName} ODBC Driver")

                                    if inWaitForUserToSetupDSN:
                                        runExecutable('odbcad32.exe')
                                    else:
                                        with winreg.CreateKeyEx(odbcIniKey, f"{inDataSourceName}", 0,
                                                                winreg.KEY_WRITE) as driverKey:
                                            for key, value in inDriverRegistryConfig.items():
                                                winreg.SetValueEx(driverKey, key, 0, winreg.REG_SZ, value)
                    return True
            else:
                print('Error: This function supports only 32 & 64 Drivers')
                return False
        else:
            print('Error: Invalid Arguments passed')
            return False


if __name__ == '__main__':
    # userName = input()
    # password = getpass()
    userName = 'Simba\\vipulr'
    password = 'Edit321@#'
    Runner(userName, password, 'input.json').run()
