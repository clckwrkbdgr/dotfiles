# Static analysis

Perform a full static-analysis compliance review of the changes against all rules in ~/.config/.github/static_analysis/cppcheck.md and ~/.config/.github/static_analysis/parasoft.md. Do not prioritize or skip any rule classes (including AUTOSAR style/const-correctness rules such as A7-1-1). Report every matching rule violation with file and line. Treat this as exhaustive rule-by-rule coverage, not a risk-prioritized review.
