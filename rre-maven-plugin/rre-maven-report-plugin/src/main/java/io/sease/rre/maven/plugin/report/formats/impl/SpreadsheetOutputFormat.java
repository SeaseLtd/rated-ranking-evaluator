package io.sease.rre.maven.plugin.report.formats.impl;

import com.fasterxml.jackson.databind.JsonNode;
import io.sease.rre.maven.plugin.report.RREMavenReport;
import io.sease.rre.maven.plugin.report.domain.EvaluationMetadata;
import io.sease.rre.maven.plugin.report.formats.OutputFormat;
import one.util.streamex.DoubleStreamEx;
import org.apache.poi.ss.usermodel.*;
import org.apache.poi.ss.util.CellRangeAddress;
import org.apache.poi.xssf.usermodel.*;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.StreamSupport;

import static io.sease.rre.maven.plugin.report.Utility.all;
import static io.sease.rre.maven.plugin.report.Utility.pretty;
import static java.util.Arrays.stream;
import static java.util.Optional.ofNullable;

/**
 * RRE Report : Excel output format.
 *
 * @author agazzarini
 * @since 1.0
 */
public class SpreadsheetOutputFormat implements OutputFormat {
    private void topHeader(final XSSFSheet sheet, EvaluationMetadata metadata) {
        final XSSFRow header = sheet.createRow(0);

        final CellStyle bold = sheet.getWorkbook().createCellStyle();
        final Font font = sheet.getWorkbook().createFont();
        font.setBold(true);
        bold.setFont(font);

        final CellStyle boldAndCentered = sheet.getWorkbook().createCellStyle();
        boldAndCentered.setFont(font);
        boldAndCentered.setAlignment(HorizontalAlignment.CENTER);

        final Cell topicHeaderCell = header.createCell(0, CellType.STRING);
        topicHeaderCell.setCellValue("Topic");
        topicHeaderCell.setCellStyle(bold);

        final Cell qgHeaderCell = header.createCell(1, CellType.STRING);
        qgHeaderCell.setCellValue("Query Group");
        qgHeaderCell.setCellStyle(bold);

        final Cell qHeaderCell = header.createCell(2, CellType.STRING);
        qHeaderCell.setCellValue("Query");
        qHeaderCell.setCellStyle(bold);

        final Cell mHeaderCell = header.createCell(3, CellType.STRING);
        mHeaderCell.setCellValue("Metric");
        mHeaderCell.setCellStyle(bold);

        try {
            sheet.addMergedRegion(
                    new CellRangeAddress(
                            header.getRowNum(),
                            header.getRowNum(),
                            3,
                            3 + (metadata.howManyMetrics() * metadata.howManyVersions())));
        } catch (final Exception ignore) {}
    }

    private void metricsHeader(final XSSFSheet sheet, final EvaluationMetadata metadata) {
        final XSSFRow header = sheet.createRow(1);

        final CellStyle bold = sheet.getWorkbook().createCellStyle();
        final XSSFFont font = sheet.getWorkbook().createFont();
        font.setBold(true);
        bold.setFont(font);
        bold.setAlignment(HorizontalAlignment.CENTER);
        font.getCTFont().addNewB();

        final AtomicInteger counter = new AtomicInteger(0);
        metadata.metrics
                .forEach(name -> {
                    final int columnIndex = 3 + (counter.getAndIncrement() * ((metadata.howManyVersions() * 2) - 1));
                    final Cell qgHeaderCell = header.createCell(columnIndex, CellType.STRING);
                    qgHeaderCell.setCellValue(name);
                    qgHeaderCell.setCellStyle(bold);
                   try {
                        sheet.addMergedRegion(
                                new CellRangeAddress(
                                        header.getRowNum(),
                                        header.getRowNum(),
                                        columnIndex,
                                        columnIndex + ((metadata.howManyVersions() * 2) - 2)));
                    } catch (final Exception ignore) {
                    }
                });
    }

    private void versionsHeader(final XSSFSheet sheet, final EvaluationMetadata metadata) {
        final XSSFRow header = sheet.createRow(2);

        final CellStyle bold = sheet.getWorkbook().createCellStyle();
        final XSSFFont font = sheet.getWorkbook().createFont();
        font.setBold(true);
        bold.setFont(font);
        bold.setAlignment(HorizontalAlignment.CENTER);
        font.getCTFont().addNewB();

        final AtomicInteger versionCounter = new AtomicInteger(3);
        metadata.metrics.forEach(metric -> {
                metadata.versions.forEach(
                        name -> {
                            final int columnIndex = versionCounter.getAndIncrement();
                            final Cell qgHeaderCell = header.createCell(columnIndex, CellType.STRING);
                            qgHeaderCell.setCellValue(name);
                            qgHeaderCell.setCellStyle(bold);
                        });

            LinkedList<Integer> deltaColumns = new LinkedList<>();
                metadata.versions
                        .stream()
                        .skip(1)
                        .forEach(name -> {
                            final int columnIndex = versionCounter.getAndIncrement();
                            deltaColumns.add(columnIndex);
                            final Cell qgHeaderCell = header.createCell(columnIndex, CellType.STRING);
                            qgHeaderCell.setCellValue("DELTA");
                            qgHeaderCell.setCellStyle(bold);
                        });
                try {
                    sheet.addMergedRegion(
                        new CellRangeAddress(
                                header.getRowNum(),
                                header.getRowNum(),
                                deltaColumns.getFirst(),
                                deltaColumns.getLast()));
                } catch (final Exception ignore) {
                }


        });
    }

    private void writeMetrics(final JsonNode ownerNode, final XSSFRow row) {
        AtomicInteger counter = new AtomicInteger();

        ownerNode.get("metrics").fields()
                .forEachRemaining(entry -> {
                    entry.getValue().get("versions").fields()
                            .forEachRemaining(vEntry -> {
                                final Cell vCell = row.createCell(3 + counter.getAndIncrement(), CellType.NUMERIC);
                                double value = vEntry.getValue().get("value").asDouble();
                                vCell.setCellValue(value);
                            });


                    final double [] delta =
                            DoubleStreamEx.of(
                                StreamSupport.stream(entry.getValue().get("versions").spliterator(), false)
                                .mapToDouble(vNode -> vNode.get("value").asDouble()))
                                .pairMap( (a, b) -> b - a).toArray();

                    stream(delta).forEach(v -> {
                        final Cell vCell = row.createCell(3 + counter.getAndIncrement(), CellType.NUMERIC);
                        vCell.setCellValue(v);
                        if (v == 0) {
                            vCell.setCellStyle(yellow);
                        } else if (v > 0) {
                            vCell.setCellStyle(green);
                        } else {
                            vCell.setCellStyle(red);
                        }
                    });
                });

    }

    private CellStyle green;
    private CellStyle red;
    private CellStyle yellow;

    @Override
    public void writeReport(final JsonNode data, EvaluationMetadata metadata, final Locale locale, final RREMavenReport plugin) {
        final XSSFWorkbook workbook = new XSSFWorkbook();
        final CellStyle topAlign = workbook.createCellStyle();
        topAlign.setVerticalAlignment(VerticalAlignment.TOP);

        final Font redFont = workbook.createFont();
        redFont.setBold(true);
        redFont.setColor(IndexedColors.RED.getIndex());

        final Font greenFont = workbook.createFont();
        greenFont.setBold(true);
        greenFont.setColor(IndexedColors.GREEN.getIndex());

        final Font yFont = workbook.createFont();
        yFont.setBold(true);
        yFont.setColor(IndexedColors.ORANGE.getIndex());

        green = workbook.createCellStyle();
        green.setFont(greenFont);

        red = workbook.createCellStyle();
        red.setFont(redFont);

        yellow = workbook.createCellStyle();
        yellow.setFont(yFont);

        all(data, "corpora")
                .forEach(corpus -> {
                    final AtomicInteger rowCount = new AtomicInteger(3);
                    final String name = corpus.get("name").asText();
                    final XSSFSheet spreadsheet = workbook.createSheet(name);

                    topHeader(spreadsheet, metadata);
                    metricsHeader(spreadsheet, metadata);
                    versionsHeader(spreadsheet, metadata);

                    final XSSFRow corpusRow = spreadsheet.createRow(rowCount.getAndIncrement());
                    // final Cell nCell = corpusRow.createCell(0, CellType.STRING);
                    //nCell.setCellValue(name);

                    writeMetrics(corpus, corpusRow);

                    all(corpus, "topics")
                            .forEach(topic -> {
                                final XSSFRow topicRow = spreadsheet.createRow(rowCount.getAndIncrement());
                                final Cell topicCell = topicRow.createCell(0, CellType.STRING);

                                final String topicName = topic.get("name").asText();
                                topicCell.setCellValue(topicName);

                                writeMetrics(topic, topicRow);

                                all(topic, "query-groups")
                                        .forEach(group -> {
                                            final XSSFRow groupRow = spreadsheet.createRow(rowCount.getAndIncrement());
                                            final Cell groupCell = groupRow.createCell(1, CellType.STRING);
                                            groupCell.setCellValue(group.get("name").asText());

                                            writeMetrics(group, groupRow);

                                            all(group, "query-evaluations")
                                                    .forEach(qeval -> {
                                                        final XSSFRow qRow = spreadsheet.createRow(rowCount.getAndIncrement());
                                                        final Cell qCell = qRow.createCell(2, CellType.STRING);
                                                        qCell.setCellValue(pretty(qeval.get("query")));

                                                        writeMetrics(qeval, qRow);
                                                    });

                                        });
                            });

                    for (int i = 0; i < (metadata.howManyVersions() * metadata.howManyMetrics() + 2); i++) {
                        spreadsheet.autoSizeColumn(i);
                    }

                    XSSFCellStyle style = workbook.createCellStyle();
                    style.setWrapText(true);
                    StreamSupport.stream(Spliterators.spliteratorUnknownSize(spreadsheet.iterator(), Spliterator.ORDERED), false)
                            .skip(5)
                            .filter(Objects::nonNull)
                            .forEach(row -> {
                                XSSFCell c = (XSSFCell) row.getCell(2);
                                ofNullable(c).ifPresent(poiCell -> {
                                    float tallestCell = -1;
                                    String value = poiCell.getStringCellValue();
                                    int numLines = 1;
                                    for (int i = 0; i < value.length(); i++) {
                                        if (value.charAt(i) == '\n') numLines++;
                                    }
                                    float cellHeight = computeRowHeightInPoints(poiCell.getCellStyle().getFont().getFontHeightInPoints(), numLines, spreadsheet);
                                    if (cellHeight > tallestCell) {
                                        tallestCell = cellHeight;
                                    }

                                    float defaultRowHeightInPoints = spreadsheet.getDefaultRowHeightInPoints();
                                    float rowHeight = tallestCell;
                                    if (rowHeight < defaultRowHeightInPoints + 1) {
                                        rowHeight = -1;    // resets to the default
                                    }

                                    row.setHeightInPoints(rowHeight);
                                });

                            });
                });



        plugin.getReportOutputDirectory().mkdirs();

        try (final OutputStream out =
                     new FileOutputStream(
                             new File(plugin.getReportOutputDirectory(), plugin.getOutputName() + ".xlsx"))) {
            workbook.write(out);
        } catch (final IOException exception) {
            throw new RuntimeException(exception);
        }
    }

    private float computeRowHeightInPoints(int fontSizeInPoints, int numLines, XSSFSheet sheet) {
        float lineHeightInPoints = 1.3f * fontSizeInPoints;
        float rowHeightInPoints = lineHeightInPoints * numLines;
        rowHeightInPoints = Math.round(rowHeightInPoints * 4) / 4f;

        float defaultRowHeightInPoints = sheet.getDefaultRowHeightInPoints();
        if (rowHeightInPoints < defaultRowHeightInPoints + 1) {
            rowHeightInPoints = defaultRowHeightInPoints;
        }
        return rowHeightInPoints;
    }
}
