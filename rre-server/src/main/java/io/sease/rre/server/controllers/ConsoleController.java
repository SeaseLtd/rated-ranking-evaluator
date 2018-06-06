package io.sease.rre.server.controllers;

import io.sease.rre.server.Func;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;

@Controller
public class ConsoleController extends BaseController {
    @Autowired
    RREController modelController;

    private Func f = new Func();

    @GetMapping("/")
    public String home(final Model model) throws Exception {
        model.addAttribute("data", modelController.getEvaluationData());
        model.addAttribute("metadata", modelController.getMetadata());
        model.addAttribute("f", f);

        return "index";
    }
}