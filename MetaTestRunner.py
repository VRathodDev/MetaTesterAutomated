import re
import os
import subprocess

from Input import InputReader
from RemoteConnection import RemoteConnection
from GenUtility import TimeOutLevel, isNoneOrEmpty, writeInFile
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
                            metatesterLogs = subprocess.check_output(command,
                                                                     timeout=TimeOutLevel.MEDIUM.value).decode()
                            if 'Done validation' in metatesterLogs:
                                return metatesterLogs
                            else:
                                print('Error: MetaTester failed to run to completion successfully')
                                print(f"For more details, "
                                      f"Check logs: {os.path.join(METATESTER_DIR, MetaTesterLogFileName)}")
                                return None

                        except subprocess.CalledProcessError as error:
                            return error.output.decode()

                        except subprocess.TimeoutExpired:
                            print(f"Error: \"{command}\" could not be executed in "
                                  f"{TimeOutLevel.MEDIUM.value / 60} Minutes!")
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
                                                                  f"MetaTesterLogs.txt")
                metaTesterLogs = MetaTester.run(pluginInfo.getDataSourceName(), pluginInfo.getPackageBitCount())
                if MetaTester.parseLogs(metaTesterLogs, logsPath):
                    summary['Plugins'][sourceFilePath]['MetaDataTest'] = 'Succeed'
                    summary['Plugins'][sourceFilePath]['MetaDataTestLogs'] = logsPath
                    print(f"{sourceFilePath}: MetaTester ran to completion successfully")
                else:
                    summary['Plugins'][sourceFilePath]['MetaDataTest'] = 'Failed'
                    summary['Plugins'][sourceFilePath]['MetaDataTestLogs'] = logsPath
                    print(f"{sourceFilePath}: MetaTester reported critical errors")
            else:
                summary['Plugins'][sourceFilePath] = 'Failed'
        remoteConnection.disconnect()
        return summary


if __name__ == '__main__':
    main(input(), getpass(), 'input.json')
