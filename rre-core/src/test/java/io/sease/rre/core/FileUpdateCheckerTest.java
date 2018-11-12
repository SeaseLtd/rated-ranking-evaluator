package io.sease.rre.core;

import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.TemporaryFolder;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.HashMap;
import java.util.Map;

import static junit.framework.TestCase.assertFalse;
import static junit.framework.TestCase.assertTrue;

public class FileUpdateCheckerTest {

    @Rule
    public TemporaryFolder tempFolder = new TemporaryFolder();

    @Test
    public void directoryHasChanged_returnsTrueWhenNoChecksumFile() throws Exception {
        final String checksumFilepath = "noSuchFile";
        final String directoryPath = tempFolder.getRoot().getPath();
        FileUpdateChecker checker = new FileUpdateChecker(checksumFilepath);

        assertTrue(checker.directoryHasChanged(directoryPath));
    }

    @Test
    public void directoryHasChanged_returnsTrueForNewDirectory() throws Exception {
        File checksumFile = tempFolder.newFile("checksums.csv");

        initialiseChecksumFile(checksumFile, 1);
        File newDir = tempFolder.newFolder();

        FileUpdateChecker checker = new FileUpdateChecker(checksumFile.getAbsolutePath());

        assertTrue(checker.directoryHasChanged(newDir.getAbsolutePath()));
    }

    @Test
    public void directoryHasChanged_returnsTrueForNewFileInDirectory() throws Exception {
        File checksumFile = tempFolder.newFile("checksums.csv");

        Map<String, String> checksums = initialiseChecksumFile(checksumFile, 3);

        String existingDirPath = checksums.keySet().iterator().next();
        // Create a new file under the first temp directory
        File tmpFile = new File(existingDirPath, "newFile.txt");
        try (final PrintWriter pw = new PrintWriter(new FileWriter(tmpFile))) {
            pw.println("Blah");
        }

        FileUpdateChecker checker = new FileUpdateChecker(checksumFile.getAbsolutePath());

        assertTrue(checker.directoryHasChanged(existingDirPath));
    }

    @Test
    public void directoryHasChanged_returnsFalseForSameDirectory() throws Exception {
        File checksumFile = tempFolder.newFile("checksums.csv");

        Map<String, String> checksums = initialiseChecksumFile(checksumFile, 3);
        String existingDirPath = checksums.keySet().iterator().next();
        FileUpdateChecker checker = new FileUpdateChecker(checksumFile.getAbsolutePath());

        assertFalse(checker.directoryHasChanged(existingDirPath));
    }

    private Map<String, String> initialiseChecksumFile(File checksumFile, int testDirCount) throws IOException {
        Map<String, String> checksums = new HashMap<>();
        for (int i = 0; i < testDirCount; i ++) {
            File testDir = tempFolder.newFolder();
            // Create a dummy file with unique text, so all checksums are different
            File tmpFile = new File(testDir, "tmp.txt");
            try (final PrintWriter pw = new PrintWriter(new FileWriter(tmpFile))) {
                pw.println("Test " + i);
            }
            String checksum = FileUpdateChecker.hashDirectory(testDir.getAbsolutePath(), false);
            checksums.put(testDir.getAbsolutePath(), checksum);
        }

        try (final PrintWriter pw = new PrintWriter(new FileWriter(checksumFile))) {
            checksums.forEach((k, v) -> pw.println(k + "," + v));
        }

        return checksums;
    }
}
