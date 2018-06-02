package io.sease.rre.maven.plugin.report.formats;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.sease.rre.maven.plugin.report.EvaluationMetadata;
import io.sease.rre.maven.plugin.report.RREReport;
import org.apache.poi.ss.usermodel.*;
import org.apache.poi.ss.util.CellRangeAddress;
import org.apache.poi.xssf.usermodel.XSSFRow;
import org.apache.poi.xssf.usermodel.XSSFSheet;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.util.Locale;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.Stream;
import java.util.stream.StreamSupport;

import static io.sease.rre.maven.plugin.report.Utility.all;
import static io.sease.rre.maven.plugin.report.Utility.pretty;

/**
 * RRE Report : Excel output format.
 *
 * @author agazzarini
 * @since 1.0
 */
public class SpreadsheetOutputFormat implements OutputFormat {
    private XSSFRow createHeader(final XSSFSheet sheet, EvaluationMetadata metadata) {
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
        } catch (final Exception ignore) {}

        return header;
    }

    private XSSFRow createSubHeader(final XSSFSheet sheet, final EvaluationMetadata metadata) {
        final XSSFRow header = sheet.createRow(0);

        final CellStyle bold = sheet.getWorkbook().createCellStyle();
        final Font font = sheet.getWorkbook().createFont();
        font.setBold(true);
        bold.setFont(font);

//        metadata.metrics.stream().forEach();
        return header;
    }

    @Override
    public void writeReport(final JsonNode data, EvaluationMetadata metadata, final Locale locale, final RREReport plugin) {
        final XSSFWorkbook workbook = new XSSFWorkbook();
        final CellStyle topAlign = workbook.createCellStyle();
        topAlign.setVerticalAlignment(VerticalAlignment.TOP);

        final AtomicInteger rowCount = new AtomicInteger(1);

        all(data, "corpora")
                .forEach(corpus -> {
                    final String name = corpus.get("name").asText();
                    final XSSFSheet spreadsheet = workbook.createSheet(name);
                    final XSSFRow header = createHeader(spreadsheet, metadata);

                    final XSSFRow corpusRow = spreadsheet.createRow(rowCount.incrementAndGet());


                    all(corpus, "topics")
                            .forEach(topic -> {
                                final XSSFRow topicRow = spreadsheet.createRow(rowCount.incrementAndGet());
                                final Cell topicCell = topicRow.createCell(0, CellType.STRING);
                                topicCell.setCellValue(topic.get("name").asText());

                                all(topic, "query-groups")
                                        .forEach(group -> {
                                            final XSSFRow groupRow = spreadsheet.createRow(rowCount.incrementAndGet());
                                            final Cell groupCell = groupRow.createCell(1, CellType.STRING);
                                            groupCell.setCellValue(group.get("name").asText());

                                            all(group, "query-evaluations")
                                                    .forEach(qeval -> {
                                                        final XSSFRow qRow = spreadsheet.createRow(rowCount.incrementAndGet());
                                                        final Cell qCell = qRow.createCell(2, CellType.STRING);
                                                        qCell.setCellValue(pretty(qeval.get("query")));
                                                        final AtomicInteger versionCount = new AtomicInteger();

                                                        all(qeval, "versions")
                                                                .forEach(version -> {
                                                                    final int howManyMetrics = version.get("metrics").size();
                                                                    final AtomicInteger metricCount = new AtomicInteger();

                                                                    all(version, "metrics")
                                                                            .forEach(metric -> {
                                                                                if (metricCount.get() % howManyMetrics == 0 ) {
                                                                                    Cell vCell = header.createCell(3 + metricCount.get() + (versionCount.get() * howManyMetrics), CellType.STRING);
                                                                                    vCell.setCellValue(version.get("name").asText());
                                                                                    vCell.setCellStyle(boldAndCentered);

                                                                                    try {
                                                                                        spreadsheet.addMergedRegion(new CellRangeAddress(header.getRowNum(), header.getRowNum(), vCell.getColumnIndex(), vCell.getColumnIndex() + (howManyMetrics -1)));
                                                                                        //irow.getCell(0).setCellStyle(topAlign);
                                                                                    } catch (final Exception ignore) {}

                                                                                    vCell.setCellStyle(boldAndCentered);

                                                                                }
                                                                                metricCount.getAndIncrement();
                                                                                final Cell hmCell = subHeader.createCell(2 + metricCount.get() + (versionCount.get() * howManyMetrics), CellType.STRING);
                                                                                hmCell.setCellValue(metric.get("name").asText());

                                                                                final Cell mCell = qRow.createCell(2 + metricCount.get() + (versionCount.get() * howManyMetrics), CellType.NUMERIC);
                                                                                mCell.setCellValue(metric.get("valueFactory").asDouble());
                                                                            });
                                                                    versionCount.incrementAndGet();
                                                                });
                                                    });
                                        });
                            });
                });
        try (final OutputStream out =
                     new FileOutputStream(
                             new File(plugin.getReportOutputDirectory(), plugin.getOutputName() + ".xlsx"))) {
            workbook.write(out);
        } catch (final IOException exception) {
            throw new RuntimeException(exception);
        }
    }
}
