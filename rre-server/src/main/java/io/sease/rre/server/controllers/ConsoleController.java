package io.sease.rre.server.controllers;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;

@Controller
public class ConsoleController extends BaseController {
    @Autowired
    RREController modelController;

    @GetMapping("/")
    public String home(final Model model) throws Exception {
        model.addAttribute("data", modelController.getEvaluationData());
        model.addAttribute("metadata", modelController.getMetadata());
        return "index";
    }
}