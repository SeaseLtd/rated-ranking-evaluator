package io.sease.rre.core;

import org.apache.commons.codec.digest.DigestUtils;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import java.io.*;
import java.nio.file.Files;
import java.util.*;

public class FileUpdateChecker {

    private final static Logger LOGGER = LogManager.getLogger(FileUpdateChecker.class);

    private final File checksumFile;
    private final Map<String, String> checksums;

    public FileUpdateChecker(String checksumFilepath) throws IOException {
        this.checksumFile = new File(checksumFilepath);
        checksums = readChecksums();
    }

    public boolean directoryHasChanged(String directoryPath) throws IOException {
        boolean ret = true;

        String dirHash = hashDirectory(directoryPath, true);
        if (checksums.containsKey(directoryPath)) {
            ret = !checksums.get(directoryPath).equals(dirHash);
        }

        checksums.put(directoryPath, dirHash);

        return ret;
    }

    private Map<String, String> readChecksums() throws IOException {
        Map<String, String> sums = new HashMap<>();

        if (!checksumFile.exists()) {
            LOGGER.warn("Checksum file " + checksumFile.getAbsolutePath() + " does not exist");
        } else {
            try (BufferedReader br = new BufferedReader(new FileReader(checksumFile))) {
                String line;
                while ((line = br.readLine()) != null) {
                    if (!line.trim().isEmpty()) {
                        String[] parts = line.split(",");
                        if (parts.length != 2) {
                            LOGGER.warn("Could not read checksum line [" + line + "]");
                        } else {
                            sums.put(parts[0], parts[1]);
                        }
                    }
                }
            }
        }

        return sums;
    }

    public void writeChecksums() throws IOException {
        if (checksums == null) {
            LOGGER.info("Skipping writeChecksums() - no checksums to write");
        } else {
            try (PrintWriter pw = new PrintWriter(new BufferedWriter(new FileWriter(checksumFile)))) {
                checksums.forEach((dir, sum) -> pw.println(dir + "," + sum));
                pw.flush();
            }
        }
    }

    static String hashDirectory(String directoryPath, boolean includeHiddenFiles) throws IOException {
        File directory = new File(directoryPath);

        if (!directory.isDirectory()) {
            throw new IllegalArgumentException("Not a directory");
        }

        Vector<FileInputStream> fileStreams = new Vector<>();
        collectFiles(directory, fileStreams, includeHiddenFiles);

        try (SequenceInputStream sequenceInputStream = new SequenceInputStream(fileStreams.elements())) {
            return DigestUtils.md5Hex(sequenceInputStream);
        }
    }

    private static void collectFiles(File directory,
                                     List<FileInputStream> fileInputStreams,
                                     boolean includeHiddenFiles) throws IOException {
        File[] files = directory.listFiles();

        if (files != null) {
            Arrays.sort(files, Comparator.comparing(File::getName));

            for (File file : files) {
                if (includeHiddenFiles || !Files.isHidden(file.toPath())) {
                    if (file.isDirectory()) {
                        collectFiles(file, fileInputStreams, includeHiddenFiles);
                    } else {
                        fileInputStreams.add(new FileInputStream(file));
                    }
                }
            }
        }
    }
}
