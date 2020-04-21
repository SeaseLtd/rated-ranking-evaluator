package io.sease.rre.persistence.impl.connector;

import org.junit.Test;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.Optional;

import static io.sease.rre.persistence.impl.connector.MappingTypeElasticsearchConnector.MAPPINGS_FILE;
import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

/**
 * Unit tests for the connector utility methods.
 *
 * @author Matt Pearce (mpearce@opensourceconnections.com)
 */
public class ConnectorUtilsTest {

    @Test
    public void getStreamReturnsEmpty_whenNoSuchFile() {
        Optional<InputStream> fileStream = ConnectorUtils.getStreamForMappingsFile("/blah");
        assertThat(fileStream).isEmpty();
    }

    @Test
    public void getStreamReturnsStream_whenFileExists() {
        Optional<InputStream> fileStream = ConnectorUtils.getStreamForMappingsFile(MAPPINGS_FILE);
        assertThat(fileStream).isPresent();
    }

    @Test(expected = IOException.class)
    public void readConfigThrowsException_whenStreamBreaks() throws IOException {
        InputStream fileStream = mock(InputStream.class);
        when(fileStream.read(any(), anyInt(), anyInt())).thenThrow(new IOException("Error"));
        ConnectorUtils.readConfig(fileStream);
    }

    @Test
    public void readConfigReturnsString_whenStreamExists() throws IOException {
        final String content = "content,\nmore content";
        InputStream stringStream = new ByteArrayInputStream(content.getBytes());
        final String output = ConnectorUtils.readConfig(stringStream);

        assertThat(output).isEqualToIgnoringWhitespace(content);
    }
}
