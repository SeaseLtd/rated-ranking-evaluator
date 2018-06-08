package io.sease.rre.server.controllers;

import io.sease.rre.server.Func;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;

@Controller
public class ConsoleController extends BaseController {
    @Autowired
    RREController modelController;

    private Func f = new Func();

    @GetMapping("/")
    public String home(final Model model, @RequestParam(name = "p", required = false) final String id) throws Exception {
        model.addAttribute("data", modelController.getEvaluationData());
        model.addAttribute("metadata", modelController.getMetadata());
        model.addAttribute("f", f);

        if (id != null) {
            model.addAttribute("id", id);
        }

        return "index";
    }
}