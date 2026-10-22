# Observed engineering challenges during this upgrade

These are observations from the October 2026 portfolio upgrade, not claims about the author's earlier collaboration.

1. **Blank React page.** The browser rendered no content after the first build. Browser logs showed a React effect cleanup error: an arrow effect returned the result of `scrollIntoView`. I changed it to a block that returns nothing and reloaded the page. The accessibility tree then showed the full homepage. Lesson: a successful TypeScript build does not prove runtime behavior.
2. **Page jumped to the chat.** The initial chat effect scrolled the whole document. I changed it to scroll the chat body only. A mobile browser inspection then showed the hero at the top. Lesson: keep scroll behavior scoped to the intended container.
3. **Python async stalled in the restricted sandbox.** Initial API tests hung at event-loop creation; a simple `asyncio.run(asyncio.sleep(0))` reproduced it. The same command ran successfully outside the restricted sandbox, and the Python suite then passed. Lesson: isolate environment failures with the smallest reproducer before changing application logic.
4. **Dependency registry unavailable in the restricted sandbox.** Initial pip and npm commands could not reach package registries. Running the declared installs with network permission succeeded. Lesson: distinguish access constraints from dependency conflicts and record the exact gate.
5. **Baseline documentation overstated repository contents.** The brief mentioned committed tests and CI, but `git ls-files` showed neither. I wrote the baseline audit and added new tests/CI rather than describing them as inherited features. Lesson: use repository evidence for portfolio claims.
