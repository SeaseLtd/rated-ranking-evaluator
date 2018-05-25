package io.sease.rre.maven.plugin.report;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.maven.plugins.annotations.LifecyclePhase;
import org.apache.maven.plugins.annotations.Mojo;
import org.apache.maven.plugins.annotations.Parameter;
import org.apache.maven.plugins.annotations.ResolutionScope;
import org.apache.maven.project.MavenProject;
import org.apache.maven.reporting.AbstractMavenReport;
import org.apache.maven.reporting.MavenReportException;
import org.apache.poi.ss.usermodel.Cell;
import org.apache.poi.ss.usermodel.CellStyle;
import org.apache.poi.ss.usermodel.CellType;
import org.apache.poi.ss.usermodel.VerticalAlignment;
import org.apache.poi.xssf.usermodel.XSSFRow;
import org.apache.poi.xssf.usermodel.XSSFSheet;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.util.HashMap;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.Stream;
import java.util.stream.StreamSupport;

@Mojo(
        name = "report",
        defaultPhase = LifecyclePhase.SITE,
        requiresDependencyResolution = ResolutionScope.RUNTIME,
        threadSafe = true
)
public class RREReport extends AbstractMavenReport {
    /**
     * Practical reference to the Maven project
     */
    @Parameter(defaultValue = "${project}", readonly = true)
    private MavenProject project;

    @Parameter(name = "format", defaultValue = "html")
    String format;

    final ObjectMapper mapper = new ObjectMapper();

    @Override
    protected void executeReport(final Locale locale) throws MavenReportException {

        final JsonNode evaluationData = evaluationAsJson();
        writeReport(evaluationData);
    }

    @Override
    public String getOutputName() {
        return "rre-report";
    }

    @Override
    public String getName(final Locale locale) {
        return "Sease - Rated Ranking Evaluator Report";
    }

    @Override
    public String getDescription(Locale locale) {
        return "N.A.";
    }

    JsonNode evaluationAsJson() throws MavenReportException {
        try {
            return mapper.readTree(evaluationOutputFile());
        } catch (final IOException exception) {
            throw new MavenReportException("Unable to load the RRE evaluation JSON payload. Are you sure RRE executed successfully?", exception);
        }
    }

    File evaluationOutputFile() throws MavenReportException {
        final File file = new File("target/rre/evaluation.json");
        if (!file.canRead()) {
            throw new MavenReportException("Unable to read RRE evaluation output file. Are you sure RRE executed successfully?");
        }
        return file;
    }

    private Stream<JsonNode> all(final JsonNode parent, final String name) {
        return StreamSupport.stream(parent.get(name).spliterator(), false);
    }

    private String pretty(final JsonNode node) {
        try {
            return mapper.writerWithDefaultPrettyPrinter().writeValueAsString(mapper.readTree(node.asText()));
        } catch (Exception exception) {
            throw new RuntimeException(exception);
        }
    }

    /**
     * Writes out the collected metrics.
     */
    private void writeReport(final JsonNode data) {
        final XSSFWorkbook workbook = new XSSFWorkbook();
        final CellStyle topAlign = workbook.createCellStyle();
        topAlign.setVerticalAlignment(VerticalAlignment.TOP);

        final Map<String, XSSFRow> rowMap = new HashMap<>();

        final AtomicInteger rowCount = new AtomicInteger();

        all(data, "corpora")
                .forEach(corpus -> {
                    final XSSFSheet spreadsheet = sheet(workbook, corpus.get("name").asText());
                    all(corpus, "topics")
                            .forEach(topic -> {
                                final XSSFRow topicRow = spreadsheet.createRow(rowCount.getAndIncrement());
                                final Cell topicCell = topicRow.createCell(0, CellType.STRING);
                                topicCell.setCellValue(topic.get("name").asText());

                                all(topic, "query-groups")
                                        .forEach(group -> {
                                            final XSSFRow groupRow = spreadsheet.createRow(rowCount.getAndIncrement());
                                            final Cell groupCell = groupRow.createCell(1, CellType.STRING);
                                            groupCell.setCellValue(group.get("name").asText());

                                            all(group, "query-evaluations")
                                                    .forEach(qeval -> {
                                                        final XSSFRow qRow = spreadsheet.createRow(rowCount.getAndIncrement());
                                                        final Cell qCell = qRow.createCell(2, CellType.STRING);
                                                        qCell.setCellValue(pretty(qeval.get("query")));

                                                        all(qeval, "versions")
                                                                .forEach(version -> {
                                                                    // TODO: scrivi 1 volta il nome della versione sulla prima riga

                                                                    final int howManyMetrics = version.get("metrics").size();
                                                                    final AtomicInteger versionCount = new AtomicInteger();
                                                                    final AtomicInteger metricCount = new AtomicInteger();

                                                                    all(version, "metrics")
                                                                            .forEach(metric -> {
                                                                                // TODO: scrivi 1 volta il nome della metrica
                                                                                final Cell mCell = qRow.createCell(3 + metricCount.getAndIncrement() + (versionCount.get() * howManyMetrics), CellType.NUMERIC);
                                                                                mCell.setCellValue(metric.get("value").asDouble());
                                                                            });
                                                                    versionCount.incrementAndGet();
                                                                });
                                                    });
                                        });
                            });
                });
        try (final OutputStream out = new FileOutputStream(new File("/Users/agazzarini/IdeaProjects/rated-ranking-evaluator/rre-maven-plugin/rre-maven-report-plugin/target/ranking_evaluation.xlsx"))) {
            workbook.write(out);
        } catch (final IOException exception) {
            throw new RuntimeException(exception);
        }

        /*
        report.forEach( (dataset, configurations) -> {
            final XSSFSheet spreadsheet = sheet(workbook, dataset);
            final AtomicInteger rowNum = new AtomicInteger(1);
            final AtomicInteger configurationCount = new AtomicInteger(-1);
            configurations.forEach((configuration, informationNeeds) -> {
                configurationCount.incrementAndGet();
                informationNeeds.forEach((informationNeed, queries) -> {
                    final XSSFRow irow =rowMap.computeIfAbsent("_i_" + dataset + "_" + informationNeed, k -> {
                        final XSSFRow row = row(spreadsheet, rowNum.incrementAndGet());
                        final Cell cell = row.createCell(0, CellType.STRING);
                        cell.setCellValue(informationNeed);
                        return row;
                    });

                    queries.forEach((query, metrics) -> {
                        final XSSFRow row = rowMap.computeIfAbsent(dataset + "_" + query, k -> {
                            final XSSFRow qrow = row(spreadsheet, rowNum.incrementAndGet());
                            final Cell qcell = qrow.createCell(1, CellType.STRING);
                            qcell.setCellValue(query);
                            return qrow;
                        });


                        final Cell p1 = row.createCell(2 + (configurationCount.get() * 6), CellType.NUMERIC);
                        p1.setCellValue(metrics.p1);

                        final Cell p2 = row.createCell(3 + (configurationCount.get() * 6), CellType.NUMERIC);
                        p2.setCellValue(metrics.p2.doubleValue());

                        final Cell p3 = row.createCell(4 + (configurationCount.get() * 6), CellType.NUMERIC);
                        p3.setCellValue(metrics.p3.doubleValue());

                        final Cell p10 = row.createCell(5 + (configurationCount.get() * 6), CellType.NUMERIC);
                        p10.setCellValue(metrics.p10.doubleValue());

                        final Cell ap = row.createCell(6 + (configurationCount.get() * 6), CellType.NUMERIC);
                        ap.setCellValue(metrics.ap.doubleValue());

                        final Cell ndcg = row.createCell(7 + (configurationCount.get() * 6), CellType.NUMERIC);
                        ndcg.setCellValue(metrics.ndcg.doubleValue());
                    });

                    try {
                        spreadsheet.addMergedRegion(new CellRangeAddress(irow.getRowNum(), irow.getRowNum() + queries.size(), 0, 0));
                        irow.getCell(0).setCellStyle(topAlign);
                    } catch (final Exception ignore) {}
                });
            });
        });

        workbook.forEach(sheet -> range(0,5).forEach(idx -> sheet.autoSizeColumn(idx)));

        try (final OutputStream out = new FileOutputStream(new File("target/ranking_evaluation.xlsx"))) {
            workbook.write(out);
        } catch (final IOException exception) {
            LOGGER.error("Unable to write the report.", exception);
        }
        */
    }

    private XSSFSheet sheet(final XSSFWorkbook workbook, final String name) {
        return workbook.createSheet(name);
            /*
        return ofNullable(workbook.getSheet(name)).orElseGet(() -> {
            final XSSFSheet sheet = ;

            final CellStyle bold = workbook.createCellStyle();
            final Font font = workbook.createFont();
            font.setBold(true);
            bold.setFont(font);

            final Row header = sheet.createRow(0);
            final Row subheader = sheet.createRow(1);
            createHeaderCell(subheader, 0, "Information Need", bold);
            createHeaderCell(subheader, 1, "Query", bold);

            AtomicInteger headerColumnNumber = new AtomicInteger(2);

            CONFIGURATION_SETS.forEach(v -> {
                createHeaderCell(header, headerColumnNumber.get(), v, bold);
                createHeaderCell(subheader, headerColumnNumber.get(), "P@1", bold);

                headerColumnNumber.incrementAndGet();
                createHeaderCell(header, headerColumnNumber.get(), "", bold);
                createHeaderCell(subheader, headerColumnNumber.get(), "P@2", bold);

                headerColumnNumber.incrementAndGet();
                createHeaderCell(header, headerColumnNumber.get(), "", bold);
                createHeaderCell(subheader, headerColumnNumber.get(), "P@3", bold);

                headerColumnNumber.incrementAndGet();
                createHeaderCell(header, headerColumnNumber.get(), "", bold);
                createHeaderCell(subheader, headerColumnNumber.get(), "P@10", bold);

                headerColumnNumber.incrementAndGet();
                createHeaderCell(header, headerColumnNumber.get(), "", bold);
                createHeaderCell(subheader, headerColumnNumber.get(), "AP", bold);

                headerColumnNumber.incrementAndGet();
                createHeaderCell(header, headerColumnNumber.get(), "", bold);
                createHeaderCell(subheader, headerColumnNumber.get(), "NDCG", bold);

                headerColumnNumber.incrementAndGet();
            });

            sheet.addMergedRegion(new CellRangeAddress(0,0,2,7));
            sheet.addMergedRegion(new CellRangeAddress(0,0,8,13));
            sheet.addMergedRegion(new CellRangeAddress(0,0,14,19));
            return sheet;
        });
    }

    private void createHeaderCell(final Row row, final int num, final String value, final CellStyle style) {
        final Cell cell = row.createCell(num);
        cell.setCellValue(value);
        cell.setCellStyle(style);
    }

    private XSSFRow row(final XSSFSheet sheet, final int num) {
        return ofNullable(sheet.getRow(num)).orElse(sheet.createRow(num));
    }
    */
    }
}