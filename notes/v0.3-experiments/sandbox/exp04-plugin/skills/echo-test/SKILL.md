---
name: echo-test
description: Canary skill for exp-04. When invoked, outputs a verification string including the passed arguments. Used to prove that --plugin-dir successfully loads a plugin skill and that the skill can be invoked from a subprocess claude -p session.
---

# echo-test (canary)

When this skill is invoked, output exactly the following single line and nothing else:

```
EXP04_CANARY_OK args=$ARGUMENTS
```

Do not add explanation, preamble, or commentary. Just that single line with the actual arguments substituted.
