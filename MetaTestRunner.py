import json
import re
import os
import subprocess
import sys

from Input import InputReader
from RemoteConnection import RemoteConnection
from GenUtility import TimeOutLevel, isNoneOrEmpty, writeInFile
from ScalabilityTestRunner import ScalabilityTestRunner


class MetaTester:

    # Global Variables
    MetaTesterDirName = 'MetaTester'

    @staticmethod
    def run(inDSN: str, inDriverBit: int, inMetaTesterDir: str):
        """
        Executes `MetaTester` \n
        :param inMetaTesterDir: Path to MetaTester.
        :param inDSN: Name of the Data Source
        :param inDriverBit: Bit count of Driver
        :return: Returns the Generated Logs during MetaTester Execution if successfully completed else None
        """
        if not isNoneOrEmpty(inDSN) and inDriverBit in [32, 64]:
            if not isNoneOrEmpty(inMetaTesterDir) and os.path.exists(inMetaTesterDir):
                MetaTesterPath = os.path.join(inMetaTesterDir, f"MetaTester{inDriverBit}.exe")
                if os.path.exists(MetaTesterPath):
                    # To generate the MetaTest logs in the `MetaTester` directory
                    # else Logs are generated at inappropriate location
                    MetaTesterLogFileName = os.path.join(inMetaTesterDir, f"{inDSN.replace(' ', '_')}_MetaTesterLogs.txt")
                    command = f"{MetaTesterPath} -d \"{inDSN}\" -o {MetaTesterLogFileName}"
                    try:
                        metatesterLogs = subprocess.check_output(command,
                                                                 timeout=TimeOutLevel.MEDIUM.value).decode().strip()
                        if 'Done validation' in metatesterLogs:
                            return metatesterLogs
                        else:
                            print('Error: MetaTester failed to run to completion successfully')
                            print(f"For more details, "
                                  f"Check logs: {MetaTesterLogFileName}")
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
                    print(f"Error: MetaTester{inDriverBit}.exe does not exist in {inMetaTesterDir}")
                    return None
            else:
                print(f"Error: Invalid Path {inMetaTesterDir}")
                return None
        else:
            print('Error: Invalid Parameters')
            return None

    @staticmethod
    def parseLogs(inLogs: str, inParsedLogFilePath: str):
        """
        Parses the `MetaTester` generated Logs\n
        :param inLogs: `MetaTester` generated Logs
        :param inParsedLogFilePath: Path to save the parsed Logs including the Log File Name
        :return: True if succeeded else False
        """
        if not isNoneOrEmpty(inLogs, inParsedLogFilePath):
            if not inParsedLogFilePath.endswith('.txt'):
                print(f"Error: {inParsedLogFilePath} must contain Log File Name with `.txt` File Extension. "
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
                        # Writes the failures count after filtration of checked ignorable Mismatches
                        currLine = f"Number of table failures: {totalFailures}\n"
                parsedLogs += currLine + '\n'

            writeInFile(parsedLogs, inParsedLogFilePath)
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


def main(inUserName: str, inPassword: str, inBasePath: str, inputFileName: str):
    if isNoneOrEmpty(inUserName, inPassword, inBasePath, inputFileName):
        print('Error: Invalid Parameter')
    elif not os.path.exists(inBasePath):
        print(f"Error: Invalid Path {inBasePath}")
    else:
        inputReader = InputReader(os.path.join(inBasePath, inputFileName))
        summary = dict()
        remoteConnection = RemoteConnection(inputReader.getRemoteMachineAddress(), inUserName, inPassword)
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
                    MetaTesterPath = os.path.join(inBasePath, MetaTester.MetaTesterDirName)
                    metaTesterLogs = MetaTester.run(pluginInfo.getDataSourceName(), pluginInfo.getPackageBitCount(),
                                                    MetaTesterPath)
                    if isNoneOrEmpty(metaTesterLogs):
                        summary['Plugins'][sourceFilePath]['MetaDataTest'] = 'Failed'
                        print(f"{sourceFilePath}: MetaTester failed to initiate")
                    else:
                        if MetaTester.parseLogs(metaTesterLogs, logsPath):
                            summary['Plugins'][sourceFilePath]['MetaDataTest'] = 'Succeed'
                            summary['Plugins'][sourceFilePath]['MetaDataTestLogs'] = logsPath
                            print(f"{sourceFilePath}: MetaTester ran to completion successfully")
                        else:
                            summary['Plugins'][sourceFilePath]['MetaDataTest'] = 'Failed'
                            summary['Plugins'][sourceFilePath]['MetaDataTestLogs'] = logsPath
                            print(f"{sourceFilePath}: MetaTester reported critical errors")

                    ScalabilityTestRunner(os.path.join(inBasePath, 'ScalabilityTester.exe'),
                                          pluginInfo.getDestinationPath(),
                                          os.path.join(pluginInfo.getLogsPath(), pluginInfo.getPackageName()) + '\\',
                                          'dsn=' + pluginInfo.getDataSourceName()).start(inBasePath)
                else:
                    summary['Plugins'][sourceFilePath] = 'Failed'
            remoteConnection.disconnect()

            with open(os.path.join(inBasePath, 'MetaTestSummary.json'), 'w') as file:
                json.dump(summary, file)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
