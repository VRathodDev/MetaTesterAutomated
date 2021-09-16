import os
import math
import subprocess
import xml.etree.ElementTree as ET


class ScalabilityTestRunner:
    def __init__(self, scalabilityTesterPath, packageLocation, outputDir, dsn):
        self.scalabilityTesterPath = scalabilityTesterPath
        self.packageLocation = packageLocation
        self.outputDir = outputDir
        self.dsn = dsn

    def start(self, inBasePath: str):
        # Prepare a batch script
        script = self.prepareBatchScript(self.getSelectQueries(1))

        # Create the Batch file
        exampleBatFile = open(os.path.join(inBasePath, 'ExampleBatchFileForST.bat'), 'w+')
        exampleBatFile.write(script)
        exampleBatFile.close()

        p = subprocess.run([os.path.join(inBasePath, 'ExampleBatchFileForST.bat')], capture_output=True)

        # Check the status of the Thread Files (Excel Files)
        if self.checkStatusOfThreadsFiles(20, 30):
            print('Done')
        else:
            print('Check the Thread Files generated')

    def prepareBatchScript(self, selectQueries):
        SCALABILITY_TESTER_PATH = self.scalabilityTesterPath
        TestNo = 0
        TEST_TIME_IN_SECONDS = 3400
        DSN = self.dsn
        OUTPUT_DIRECTORY = self.outputDir
        THREAD_COUNT = 30

        script = "@echo off\n"
        script += "cls\n\n"

        script += "Set TestNo=" + str(TestNo) + "\n"
        script += "Set TEST_TIME_IN_SECONDS=" + str(TEST_TIME_IN_SECONDS) + "\n"
        script += "Set SCALABILITY_TESTER_PATH=" + SCALABILITY_TESTER_PATH + "\n"
        script += "Set DSN=\"" + DSN + "\"\n"
        script += "Set OUTPUT_DIRECTORY=" + OUTPUT_DIRECTORY + "\n"
        script += "Set THREAD_COUNT=" + str(THREAD_COUNT) + "\n\n"

        script += ":start\n"
        script += "Set OUTPUT_FILE=\"%OUTPUT_DIRECTORY%" + "%TestNo%\n"

        for query in selectQueries:
            script += "if %TestNo% == " + str(TestNo)
            script += " %SCALABILITY_TESTER_PATH% -t %THREAD_COUNT%" + " -dc %DSN% -q \"" + query + "\""
            script += " -tt %TEST_TIME_IN_SECONDS%" + " -o %OUTPUT_FILE%\n"
            TestNo += 1

        script += "if %TestNo% == " + str(TestNo) + " goto end\n\n"

        script += "Set /A TestNo+=1\n"
        script += "goto start\n\n"

        script += ":end\n"
        script += "echo \"Done.\"\n"
        # script += "pause\n"

        return script

    def checkStatusOfThreadsFiles(self, n_cycles, n_threads):
        status = True

        for cycleNumber in range(0, n_cycles):
            cycleFoldarPath = self.outputDir + str(cycleNumber)
            if os.path.isdir(cycleFoldarPath):
                for threadNumber in range(1, n_threads + 1):
                    threadFilePath = cycleFoldarPath + "\\Thread_" + str(threadNumber) + ".csv"
                    if os.path.isfile(threadFilePath):
                        fileSize = math.ceil(os.stat(threadFilePath).st_size / 1000)  # Convert bytes to KBs
                        if fileSize <= 1:
                            status = False
                            break
            if status == False:
                break

        return status

    def getSelectQueries(self, n_queries):
        # Get required test sets from the package location
        SQL_TestSets = self.getSQLTestSets()

        # Get the required amount of the test sets from the test sets
        selectQueries = self.getQueries(SQL_TestSets, n_queries)

        return selectQueries

    def getSQLTestSets(self):
        testSets_Dir = self.packageLocation + "\\Touchstone\\specific\\TestDefinitions\\SQL\\TestSets"

        SQL_TestSets = []  # The Test Sets such as AND_OR, JOIN, LIKE, PASSDOWN, SELECT_TOP, GROUP_BY, ORDER_BY

        for filename in os.listdir(testSets_Dir):
            if filename.endswith('.xml') and filename.startswith('SQL_'):
                f = os.path.join(testSets_Dir, filename)
                if os.path.isfile(f):
                    SQL_TestSets.append(str(f))

        # Replace all the testSetFilePaths with the xml parsed roots which is in this case a <TestSet>
        for fileIndex, testSetFilePath in enumerate(SQL_TestSets):
            parsedTestSetFile = ET.parse(testSetFilePath)
            testSet = parsedTestSetFile.getroot()
            SQL_TestSets[fileIndex] = testSet

        return SQL_TestSets

    def getQueries(self, SQL_TestSets, n_queries):
        selectQueries = []  # should contain 20 select queries for Scalability Test.

        # Pick the 20 queries required for the Scalibility Test.
        no_of_queries = 0
        while no_of_queries < n_queries:
            querynumber = 1
            for testSet in SQL_TestSets:
                if no_of_queries >= n_queries: break
                query = testSet[querynumber - 1].find('SQL').text
                if 'select' in query.lower():
                    selectQueries.append(query)
                    no_of_queries += 1
            if no_of_queries >= n_queries: break
            querynumber += 1

        return selectQueries