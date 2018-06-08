package io.sease.rre.server.velocity;

import org.apache.velocity.VelocityContext;
import org.apache.velocity.context.Context;
import org.apache.velocity.tools.view.XMLToolboxManager;
import org.apache.velocity.tools.view.context.ChainedContext;
import org.springframework.web.servlet.view.velocity.VelocityLayoutView;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.util.Map;

@SuppressWarnings("deprecation")
public class CustomVelocityLayoutView extends VelocityLayoutView {
	/**
	 * Overridden to create a ChainedContext, which is part of the view package
	 * of Velocity Tools, as special context. ChainedContext is needed for
	 * initialization of ViewTool instances.
	 * @see #initTool
	 */

	@Override
	protected Context createVelocityContext(
			Map<String, Object> model, HttpServletRequest request, HttpServletResponse response) throws Exception {

		// Create a ChainedContext instance.
		ChainedContext velocityContext = new ChainedContext(
				new VelocityContext(model), getVelocityEngine(), request, response, getServletContext());

		// Load a Velocity Tools toolbox, if necessary.
		if (getToolboxConfigLocation() != null) {
			XMLToolboxManager toolboxManager = new XMLToolboxManager();
			toolboxManager.load(getClass().getResourceAsStream(getToolboxConfigLocation()));			
			Map<String, Object> toolboxContext = toolboxManager.getToolbox(velocityContext);
			velocityContext.setToolbox(toolboxContext);
		}

		return velocityContext;
	}
}
