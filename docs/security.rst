.. _security:

========
Security
========

Alligator takes security seriously. By default, it:

* does not access your filesystem in any way.
* only handles JSON-serializable data.
* only imports code available to your ``PYTHONPATH``.

While no known vulnerabilities exist, all software has bugs & Alligator is no
exception.

If you believe you have found a security-related issue, please **DO NOT SUBMIT
AN ISSUE/PULL REQUEST**. This would be a public disclosure & would allow for
0-day exploits.

Instead, please send an email to "daniel@toastdriven.com" & include the
following information:

* A description of the problem/suggestion.
* How to recreate the bug.
* If relevant, including the versions of your:

  * Python interpreter
  * Web framework (if applicable)
  * Alligator
  * Optionally of the other dependencies involved

Please bear in mind that I'm not a security expert/researcher, so a layman's
description of the issue is very important.

Upon reproduction of the exploit, steps will be taken to fix the issue, release
a new version & make users aware of the need to upgrade. Proper credit for the
discovery of the issue will be granted via the AUTHORS file & other mentions.
