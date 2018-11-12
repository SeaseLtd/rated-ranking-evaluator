package io.sease.rre;

import java.io.File;
import java.io.IOException;
import java.nio.file.*;
import java.nio.file.attribute.BasicFileAttributes;
import java.util.Objects;

public class DirectoryUtils {

    /**
     * Recursively delete a directory. Will silently ignore directories that
     * don't exist.
     *
     * @param deleteDir the directory to be deleted.
     * @throws IOException if there are problems deleting the directory.
     */
    public static void deleteDirectory(File deleteDir) throws IOException {
        if (deleteDir.exists()) {
            Path directory = Paths.get(deleteDir.toURI());
            Files.walkFileTree(directory, new SimpleFileVisitor<Path>() {
                @Override
                public FileVisitResult visitFile(Path file, BasicFileAttributes attrs) throws IOException {
                    Files.delete(file);
                    return FileVisitResult.CONTINUE;
                }

                @Override
                public FileVisitResult postVisitDirectory(Path dir, IOException exc) throws IOException {
                    Files.delete(dir);
                    return FileVisitResult.CONTINUE;
                }
            });
        }
    }

    public static void copyDirectory(File sourceLocation , File targetLocation) throws IOException {
        if (sourceLocation.isDirectory()) {
            if (!targetLocation.exists()) {
                Files.createDirectory(targetLocation.toPath());
            }

            for (String child : Objects.requireNonNull(sourceLocation.list())) {
                copyDirectory(new File(sourceLocation, child), new File(targetLocation, child));
            }
        } else {
            Files.copy(sourceLocation.toPath(), targetLocation.toPath());
        }
    }
}
