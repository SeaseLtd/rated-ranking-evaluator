package io.sease.rre.server;

import io.sease.rre.server.velocity.CustomVelocityLayoutView;
import io.sease.rre.server.velocity.CustomVelocityLayoutViewResolver;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.env.Environment;
import org.springframework.web.servlet.config.annotation.*;
import org.springframework.web.servlet.view.velocity.VelocityConfigurer;
import org.springframework.web.servlet.view.velocity.VelocityViewResolver;

import java.util.Properties;

@EnableWebMvc
@Configuration
public class WebApplicationConfiguration extends WebMvcConfigurerAdapter {
	
	@Autowired
	private Environment env;
	
    @Override
    public void addViewControllers(ViewControllerRegistry registry) {
        registry.addViewController("/").setViewName("index");
    }
	
    @Override
    public void addResourceHandlers(ResourceHandlerRegistry registry) {
        registry
          .addResourceHandler("/**","/webjars/**","/**/favicon.ico")
          .addResourceLocations("/", "classpath:/META-INF/resources/", "classpath:/resources/", "classpath:/static/", "classpath:/public/");
    }
	
    @Override
    public void configureDefaultServletHandling(DefaultServletHandlerConfigurer configurer) {
        configurer.enable();
    }
    
	@Bean 
	public VelocityViewResolver viewResolver() { 
		CustomVelocityLayoutViewResolver resolver = new CustomVelocityLayoutViewResolver();
	    resolver.setCache(true); 
	    resolver.setViewClass(CustomVelocityLayoutView.class);
	    resolver.setLayoutUrl("Default.vm");
	    resolver.setToolboxConfigLocation("/toolbox.xml");
	    resolver.setPrefix(""); 
	    resolver.setContentType("text/html;utf-8");
	    resolver.setSuffix(".vm"); 
	    return resolver; 
	}

	@Bean
    public VelocityConfigurer velocityConfig() {
        VelocityConfigurer configurer = new VelocityConfigurer();
        configurer.setResourceLoaderPath("classpath:/templates");
        Properties p = new Properties();
        p.setProperty("input.encoding", "UTF-8");
        p.setProperty("output.encoding", "UTF-8");
        p.setProperty("velocimacro.library", "VM_global_library.vm");
        configurer.setVelocityProperties(p);
        return configurer;
    }	
}