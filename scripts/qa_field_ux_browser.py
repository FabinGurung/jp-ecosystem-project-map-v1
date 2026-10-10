#!/usr/bin/env python3
"""Repeatable field-first public UI browser checks.

Runs against a local HTTP serving checkout contents. Chrome (preinstalled
on GitHub runners) is driven by Playwright; private Drive bytes are never
downloaded or included in screenshot artifacts.
"""
import os
import pathlib
import shutil
import subprocess
import sys
import time
import urllib.request
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8878"
OUT = pathlib.Path("artifacts/field-ux")
OUT.mkdir(parents=True, exist_ok=True)

def require(condition, message):
    if not condition:
        raise AssertionError(message)

def ready(server):
    for _ in range(40):
        if server.poll() is not None:
            raise RuntimeError("Local HTTP server exited")
        try:
            with urllib.request.urlopen(BASE + "/site-operations.html", timeout=1) as r:
                if r.status == 200:
                    return
        except OSError:
            pass
        time.sleep(0.25)
    raise RuntimeError("Local HTTP server not ready")

def audit_wcag(page, label):
    axe_path=pathlib.Path("node_modules/axe-core/axe.min.js")
    require(axe_path.exists(), "axe-core missing from UI QA runner")
    page.add_script_tag(path=str(axe_path))
    report=page.evaluate("""async () => {
      const result=await axe.run(document, {
        runOnly: {type: "tag", values:["wcag2a","wcag2aa","wcag21a","wcag21aa","wcag22aa"]},
        resultTypes:["violations"]
      });
      return result.violations.map(v=>({
        id:v.id, impact:v.impact,
        nodes:v.nodes.slice(0,5).map(n=>({selector:n.target,summary:n.failureSummary}))
      }));
    }""")
    print("WCAG_AUDIT",label,"violations",len(report))
    for v in report:
        print("WCAG_FINDING",label,v["id"],v["impact"],str(v["nodes"])[:280])
    fatal=[v for v in report if v["impact"] in {"critical","serious"}]
    require(not fatal, f"{label}: serious or critical WCAG errors: {[x['id'] for x in fatal]}")
    return report

def screenshot(page, name):
    dest=OUT/name
    page.screenshot(path=str(dest), full_page=True, animations="disabled", timeout=25000)
    require(dest.exists() and dest.stat().st_size > 5000, "Screenshot missing: " + str(dest))
    print("SCREENSHOT", dest, dest.stat().st_size, "bytes")

def no_wide_overflow(page, desc, tolerance=18):
    dims=page.evaluate("""() => ({
      window: window.innerWidth,
      html: document.documentElement.scrollWidth,
      body: document.body.scrollWidth
    })""")
    print("DIMENSIONS", desc, dims)
    require(dims["html"] <= dims["window"]+tolerance, f"{desc} horizontal html overflow {dims}")
    intended=page.viewport_size["width"]
    require(dims["html"] <= intended+2, f"{desc} exceeds specified {intended}px viewport: {dims}")

def run():
    server=subprocess.Popen([sys.executable,"-m","http.server","8878","--bind","127.0.0.1"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    try:
        ready(server)
        with sync_playwright() as pw:
            binary=shutil.which("google-chrome") or shutil.which("google-chrome-stable") or shutil.which("chromium")
            require(binary is not None, "Chromium/Chrome is not installed")
            browser=pw.chromium.launch(executable_path=binary, headless=True, args=[
                "--no-sandbox","--disable-dev-shm-usage","--disable-gpu"
            ],timeout=30000)
            try:
                desktop=browser.new_context(viewport={"width":1440,"height":900}, reduced_motion="reduce")
                page=desktop.new_page()
                page.goto(BASE+"/site-operations.html",wait_until="domcontentloaded",timeout=20000)
                page.wait_for_function("() => document.querySelectorAll('#project option').length >= 8",timeout=18000)
                require(page.locator("#project option").count()==8,"Project selection should contain eight sites")
                require(page.locator("h1").inner_text()=="Checklist for Today","Daily Checklist title missing")
                require(page.locator("#tasks input[type=checkbox]").count()==0,"User checklist must start empty")
                require(page.locator("#count").inner_text().startswith("No tasks yet"),"Empty state missing")
                page.locator("#new-task").fill("Confirm today's site toolbox instructions")
                page.locator("#add-form button").click()
                require(page.locator("#tasks input[type=checkbox]").count()==1,"Author-entered checklist not added")
                page.locator("#tasks input[type=checkbox]").first.check()
                require(page.locator("#count").inner_text().startswith("1 / 1"),"User checklist checked state missing")
                page.reload(wait_until="domcontentloaded")
                page.locator("#tasks input[type=checkbox]").first.wait_for(timeout=18000)
                require(page.locator("#tasks input[type=checkbox]").first.is_checked(),"Local browser task persistence failed")
                page.locator("#project").select_option("P004")
                require(page.locator("#tasks input[type=checkbox]").count()==0,"Checklist leaked between sites")
                require(page.locator('a[href="site-operations/coordination.html"]').count()>=1,"Site Coordination link missing")
                require(page.locator('a[href="site-operations/history.html"]').count()>=1,"Progress Report link missing")
                no_wide_overflow(page,"daily checklist desktop")
                audit_wcag(page,"daily checklist")
                screenshot(page,"site-daily-checklist-desktop.png")
                print("PASS: user-authored empty checklist, local browser entry and per-project isolation")

                page.goto(BASE+"/site-operations/coordination.html?project=P004",wait_until="domcontentloaded",timeout=20000)
                page.locator("#issues .item").first.wait_for(timeout=18000)
                require(page.locator("#issues .item").count()==2,"Yamuna should have two source issues")
                require(page.locator("#questions .item").count()==3,"Yamuna should have three follow-up questions")
                require(page.locator("#project").input_value()=="P004","Project deep link not retained")
                audit_wcag(page,"site coordination")
                screenshot(page,"site-coordination-desktop.png")

                page.goto(BASE+"/site-operations/history.html?project=P002",wait_until="domcontentloaded",timeout=20000)
                page.locator("#history details.entry").first.wait_for(timeout=18000)
                require(page.locator("h1").inner_text()=="Progress Report","Progress Report heading missing")
                require(page.locator("#history details.entry").count()==1,"Samir history should contain one indexed report")
                require(page.locator("#carryover-records .carry-record").count()==0 or page.locator("#carry-count").inner_text().startswith("4 archived"),"Samir carryover index unexpected")
                page.locator("#carryover-records .carry-project").first.locator("summary").click()
                require(page.locator("#carryover-records .carry-record").count()==4,"Four Samir checklist items should appear under Progress Report")
                page.locator("#history details.entry summary").first.click()
                require(page.locator("#history details.entry").first.get_attribute("open") is not None,"History expansion failed")
                audit_wcag(page,"progress report")
                screenshot(page,"progress-report-desktop.png")

                page.goto(BASE+"/site-operations/questions.html?project=P002",wait_until="domcontentloaded",timeout=20000)
                page.locator("#board article.card").first.wait_for(timeout=18000)
                require(page.locator("#board article.card").count()==6,"Samir detailed answers filtered to six questions")
                audit_wcag(page,"detailed engineer questions")
                page.goto(BASE+"/site-operations/schedule.html?project=P002",wait_until="domcontentloaded",timeout=20000)
                page.locator("#site-cards article.card").first.wait_for(timeout=18000)
                require(page.locator("#site-cards article.card").count()==1,"Legacy Samir detailed hold view broken")
                audit_wcag(page,"legacy work and holds")

                page.goto(BASE+"/site-operations/project.html?project=P007",wait_until="domcontentloaded",timeout=20000)
                page.locator("#drawings .resource-card").first.wait_for(timeout=18000)
                require(page.locator("#drawings .resource-card").count()>=11,"P007 document pointers missing")
                require(page.locator("#work .day-panel").count()==3, "Yesterday, Today and Tomorrow panels missing")
                require(page.locator("#work .schedule-table").count()>=2, "Expected yesterday and today trade tables")
                require(page.locator("#work .schedule-table tbody tr").count()>=5, "Expected source-grounded trade rows")
                require(page.locator(".gate-grid").count()==0, "Old unknown PPE/tools/manpower gates must not return")
                require(page.locator("#blockers .issues-table tbody tr").count()>=2, "Trade-specific issue queue missing")
                require(page.locator(".resource-optional").count()>=3,"Optional discipline disclosures missing")
                require(not page.locator(".resource-optional").first.evaluate("(e)=>e.open"),"Optional models should start collapsed")
                page.locator(".resource-optional").first.locator("summary").click()
                require(page.locator(".resource-optional").first.evaluate("(e)=>e.open"),"Optional model disclosure failed")
                page.locator(".resource-optional").first.locator("summary").click()
                require(page.locator("#historical-records").get_attribute("open") is None,"History unexpectedly expanded")
                page.locator("#historical-records summary").click()
                require(page.locator("#historical-records").get_attribute("open") is not None,"Progress disclosure did not open")
                page.locator("#historical-records summary").click()
                require(page.locator("#historical-records").get_attribute("open") is None,"Progress disclosure did not close")
                require(page.locator("#work").count()==1 and page.locator("#blockers").count()==1,"Field brief missing work or holds")
                no_wide_overflow(page,"P007 desktop")
                audit_wcag(page,"project brief")
                screenshot(page, "narayani-brief-desktop.png")
                print("PASS: Narayani field plan, project documents and collapsed history")

                mobile=browser.new_context(viewport={"width":390,"height":844},device_scale_factor=1,
                                            is_mobile=True,has_touch=True,reduced_motion="reduce")
                m=mobile.new_page()
                m.goto(BASE+"/site-operations.html",wait_until="domcontentloaded",timeout=20000)
                m.wait_for_function("() => document.querySelectorAll('#project option').length >= 8",timeout=18000)
                require(m.locator("#project option").count()==8,"Mobile user checklist project choices missing")
                require(m.locator("#tasks input[type=checkbox]").count()==0,"Mobile checklist should start empty")
                no_wide_overflow(m,"field desk mobile")
                screenshot(m,"site-daily-checklist-mobile.png")
                m.goto(BASE+"/site-operations/project.html?project=P007",wait_until="domcontentloaded",timeout=20000)
                m.locator("#drawings .resource-card").first.wait_for(timeout=18000)
                no_wide_overflow(m,"Narayani mobile")
                screenshot(m,"narayani-brief-mobile.png")
                print("PASS: field brief mobile snapshots and horizontal-overflow constraints")

                # Map may require the remotely hosted Leaflet library and OSM tiles.
                # A failed external asset is an explicit error, not a successful visual certification.
                page.goto(BASE+"/map.html",wait_until="domcontentloaded",timeout=25000)
                page.locator(".leaflet-container").wait_for(timeout=25000)
                # Wait for a useful amount of background imagery; Leaflet container alone
                # does not prove tiles finished loading.
                page.wait_for_function("() => document.querySelectorAll('img.leaflet-tile-loaded').length >= 8",timeout=18000)
                print("MAP_TILES_DESKTOP",page.locator("img.leaflet-tile-loaded").count())
                require(page.locator("#workspace").evaluate("(e)=>e.classList.contains('list-collapsed')"),
                        "Map did not start map-first")
                require(page.locator("#project-pane").is_hidden(),"Project list visible by default")
                audit_wcag(page,"map")
                screenshot(page,"map-first-desktop.png")
                page.locator("#map-list-button").click()
                require(page.locator("#map-list-button").get_attribute("aria-expanded")=="true",
                        "Map list button aria state did not update")
                require(page.locator("#project-pane").is_visible(),"Map project list failed to open")
                page.locator("#map-list-button").click()
                require(page.locator("#project-pane").is_hidden(),"Map project list failed to close")
                page.locator("#filter-toggle").click()
                require(page.locator("#map-controls").is_visible(),"Map filters did not open")
                page.locator("#filter-toggle").click()
                require(not page.locator("#map-controls").is_visible(),"Map filters did not close")
                page.locator(".map-layer-control summary").click()
                require(page.locator("#layer-projects").is_visible(),"Map layer disclosure failed")
                no_wide_overflow(page,"map desktop")
                print("PASS: map first, optional list, filters and layer disclosure")
                m.goto(BASE+"/map.html",wait_until="domcontentloaded",timeout=25000)
                m.locator(".leaflet-container").wait_for(timeout=25000)
                m.wait_for_function("() => document.querySelectorAll('img.leaflet-tile-loaded').length >= 3",timeout=18000)
                print("MAP_TILES_MOBILE",m.locator("img.leaflet-tile-loaded").count())
                require(m.locator("#project-pane").is_hidden(),"Mobile map list not initially collapsed")
                no_wide_overflow(m,"map mobile",tolerance=22)
                audit_wcag(m,"map mobile")
                screenshot(m,"map-first-mobile.png")
                print("PASS: map mobile screenshot and disclosure default")
                mobile.close()
                desktop.close()
            finally:
                browser.close()
    finally:
        server.terminate()
        try: server.wait(timeout=4)
        except subprocess.TimeoutExpired: server.kill()
    print("PASS: visual, responsive, accessibility-control smoke and field interactions")

if __name__=="__main__":
    run()
