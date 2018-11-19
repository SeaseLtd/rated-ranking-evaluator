package io.sease.rre.core;

import org.apache.commons.codec.digest.DigestUtils;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import java.io.*;
import java.nio.file.Files;
import java.util.*;

/**
 * Manager class to track updates to configuration files.
 *
 * @author Matt Pearce (matt@flax.co.uk)
 */
public class FileUpdateChecker {

    private final static Logger LOGGER = LogManager.getLogger(FileUpdateChecker.class);

    private final File checksumFile;
    private final Map<String, String> checksums;

    /**
     * Initialise the class with a checksum file. The checksums are read
     * immediately - if the file does not exist, it will be created, otherwise
     * the checksums will be read from the file.
     *
     * @param checksumFilepath the path to the checksum file in use. Set in
     *                         config in the pom.xml.
     * @throws IOException if the file exists and cannot be read.
     */
    public FileUpdateChecker(String checksumFilepath) throws IOException {
        this.checksumFile = new File(checksumFilepath);
        checksums = readChecksums();
    }

    /**
     * Check whether a directory has changed since its checksum was written.
     *
     * @param directoryPath the path to the directory.
     * @return {@code true} if the directory's checksum does not match the
     * stored checksum.
     * @throws IOException if the directory cannot be read.
     */
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

    /**
     * Write the current checksums to the checksum file.
     *
     * @throws IOException if the file cannot be written.
     */
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

    /**
     * Create a hash for the given directory, including all files and
     * directories contained inside, optionally including or excluding
     * hidden files.
     * <p>
     * Code taken from this Stackoverflow answer: https://stackoverflow.com/a/46899517
     *
     * @param directoryPath      the path to the directory to be hashed.
     * @param includeHiddenFiles should hidden files be included?
     * @return a string containing the hash of the directory, including all of
     * its files.
     * @throws IOException if the directory or any of its files cannot be
     *                     read.
     */
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
