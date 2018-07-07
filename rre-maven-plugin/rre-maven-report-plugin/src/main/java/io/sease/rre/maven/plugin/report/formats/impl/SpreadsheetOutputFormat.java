package io.sease.rre.maven.plugin.report.formats.impl;

import com.fasterxml.jackson.databind.JsonNode;
import io.sease.rre.maven.plugin.report.RREMavenReport;
import io.sease.rre.maven.plugin.report.domain.EvaluationMetadata;
import io.sease.rre.maven.plugin.report.formats.OutputFormat;
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
import static java.util.Optional.ofNullable;

/**
 * RRE Report : Excel output format.
 *
 * @author agazzarini
 * @since 1.0
 */
public class SpreadsheetOutputFormat implements OutputFormat {
    private XSSFRow topHeader(final XSSFSheet sheet, EvaluationMetadata metadata) {
        final XSSFRow header = sheet.createRow(0);

        final CellStyle bold = sheet.getWorkbook().createCellStyle();
        final Font font = sheet.getWorkbook().createFont();
        font.setBold(true);
        bold.setFont(font);

        final CellStyle boldAndCentered = sheet.getWorkbook().createCellStyle();
        boldAndCentered.setFont(font);
        boldAndCentered.setAlignment(HorizontalAlignment.CENTER);

        final Cell corpusHeaderCell = header.createCell(0, CellType.STRING);
        corpusHeaderCell.setCellValue("Corpus");
        corpusHeaderCell.setCellStyle(bold);

        final Cell topicHeaderCell = header.createCell(1, CellType.STRING);
        topicHeaderCell.setCellValue("Topic");
        topicHeaderCell.setCellStyle(bold);

        final Cell qgHeaderCell = header.createCell(2, CellType.STRING);
        qgHeaderCell.setCellValue("Query Group");
        qgHeaderCell.setCellStyle(bold);

        final Cell qHeaderCell = header.createCell(3, CellType.STRING);
        qHeaderCell.setCellValue("Query");
        qHeaderCell.setCellStyle(bold);

        final Cell mHeaderCell = header.createCell(4, CellType.STRING);
        mHeaderCell.setCellValue("Metric");
        mHeaderCell.setCellStyle(bold);

        try {
            sheet.addMergedRegion(
                    new CellRangeAddress(
                            header.getRowNum(),
                            header.getRowNum(),
                            4,
                            4 + (metadata.howManyMetrics() * metadata.howManyVersions())));
        } catch (final Exception ignore) {
        }

        return header;
    }

    private XSSFRow metricsHeader(final XSSFSheet sheet, final EvaluationMetadata metadata) {
        final XSSFRow header = sheet.createRow(1);

        final CellStyle bold = sheet.getWorkbook().createCellStyle();
        final Font font = sheet.getWorkbook().createFont();
        font.setBold(true);
        bold.setFont(font);
        bold.setAlignment(HorizontalAlignment.CENTER);

        final AtomicInteger counter = new AtomicInteger(0);
        metadata.metrics
                .forEach(name -> {
                    final int columnIndex = 4 + (counter.getAndIncrement() * metadata.howManyVersions());
                    final Cell qgHeaderCell = header.createCell(columnIndex, CellType.STRING);
                    qgHeaderCell.setCellValue(name);
                    qgHeaderCell.setCellStyle(bold);
                    try {
                        sheet.addMergedRegion(
                                new CellRangeAddress(
                                        header.getRowNum(),
                                        header.getRowNum(),
                                        columnIndex,
                                        columnIndex + (metadata.howManyVersions() - 1)));
                    } catch (final Exception ignore) {
                    }
                });
        return header;
    }

    private XSSFRow versionsHeader(final XSSFSheet sheet, final EvaluationMetadata metadata) {
        final XSSFRow header = sheet.createRow(2);

        final CellStyle bold = sheet.getWorkbook().createCellStyle();
        final Font font = sheet.getWorkbook().createFont();
        font.setBold(true);
        bold.setFont(font);
        final AtomicInteger versionCounter = new AtomicInteger(4);
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
                                deltaColumns.getFirst() + deltaColumns.size()));
                } catch (final Exception ignore) {
                }


        });
        return header;
    }

    private void writeMetrics(final JsonNode ownerNode, final XSSFRow row) {
        AtomicInteger counter = new AtomicInteger();
        ownerNode.get("metrics").fields()
                .forEachRemaining(entry -> {
                    final List<Double> delta = new ArrayList<>();
                    entry.getValue().get("versions").fields()
                            .forEachRemaining(vEntry -> {
                                final Cell vCell = row.createCell(4 + counter.getAndIncrement(), CellType.NUMERIC);
                                double value = vEntry.getValue().get("value").asDouble();
                                vCell.setCellValue(value);
                            });
                });

    }

    @Override
    public void writeReport(final JsonNode data, EvaluationMetadata metadata, final Locale locale, final RREMavenReport plugin) {
        final XSSFWorkbook workbook = new XSSFWorkbook();
        final CellStyle topAlign = workbook.createCellStyle();
        topAlign.setVerticalAlignment(VerticalAlignment.TOP);

        final AtomicInteger rowCount = new AtomicInteger(3);

        all(data, "corpora")
                .forEach(corpus -> {
                    final String name = corpus.get("name").asText();
                    final XSSFSheet spreadsheet = workbook.createSheet(name);

                    topHeader(spreadsheet, metadata);
                    metricsHeader(spreadsheet, metadata);
                    versionsHeader(spreadsheet, metadata);

                    final XSSFRow corpusRow = spreadsheet.createRow(rowCount.getAndIncrement());
                    final Cell nCell = corpusRow.createCell(0, CellType.STRING);
                    nCell.setCellValue(name);

                    writeMetrics(corpus, corpusRow);

                    all(corpus, "topics")
                            .forEach(topic -> {
                                final XSSFRow topicRow = spreadsheet.createRow(rowCount.getAndIncrement());
                                final Cell topicCell = topicRow.createCell(1, CellType.STRING);
                                topicCell.setCellValue(topic.get("name").asText());

                                writeMetrics(topic, topicRow);


                                all(topic, "query-groups")
                                        .forEach(group -> {
                                            final XSSFRow groupRow = spreadsheet.createRow(rowCount.getAndIncrement());
                                            final Cell groupCell = groupRow.createCell(2, CellType.STRING);
                                            groupCell.setCellValue(group.get("name").asText());

                                            writeMetrics(group, groupRow);

                                            all(group, "query-evaluations")
                                                    .forEach(qeval -> {
                                                        final XSSFRow qRow = spreadsheet.createRow(rowCount.getAndIncrement());
                                                        final Cell qCell = qRow.createCell(3, CellType.STRING);
                                                        qCell.setCellValue(pretty(qeval.get("query")));

                                                        writeMetrics(qeval, qRow);
                                                    });

                                        });
                            });

                    for (int i = 0; i < (metadata.howManyVersions() * metadata.howManyMetrics() + 4); i++) {
                        spreadsheet.autoSizeColumn(i);
                    }

                    XSSFCellStyle style = workbook.createCellStyle();
                    style.setWrapText(true);
                    StreamSupport.stream(Spliterators.spliteratorUnknownSize(spreadsheet.iterator(), Spliterator.ORDERED), false)
                            .skip(5)
                            .filter(Objects::nonNull)
                            .forEach(row -> {
                                XSSFCell c = (XSSFCell) row.getCell(3);
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
