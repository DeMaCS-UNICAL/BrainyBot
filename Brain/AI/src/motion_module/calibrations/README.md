The calibrationf follow the pattern:
- Test: test_{n_}
- Robot: brainybot1 / brainybot2
- Pen: garbage1 / garbage2 
- Suffix: stuff you want

Other stuff appended before .pkl will be ignored
Information like: 
- automatic/manual deep 
- parameters used

The search function will only match Robot and Pen so if 2 file with the sane starting name exists will take one randomly
If you need different calibrations for the same bot/pen use the test_enumarator