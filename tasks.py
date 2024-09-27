import invoke

@invoke.tasks.task()
def save_screenshot(ctx: invoke.context.Context):
    out = "screenshot.png"
    url = "http://localhost:4321/"
    size = "1920,1080"
    subprocess.run(
        f"chromium --headless --screenshot={out} --window-size={size} --hide-scrollbars --timeout=1100 {url}".split(" ")
    )

