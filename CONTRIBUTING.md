# Contributing

We love pull requests from everyone.  
Fork, then clone the repo:

    git clone git@github.com:your-username/telewall.git

Set up pyton env:

    virtualenv -p /usr/bin/python2.7 py2-env
    source py2-env/bin/activate
    pip install -r telewall/requirements.txt

Make sure the tests pass:

    bin/run-tests.sh

Make your change. Add tests for your change. Make the tests pass:

    run-tests.sh

Push to your fork and [submit a pull request][pr].

[pr]: https://github.com/synox/telewall/compare/

At this point you're waiting on us. We like to at least comment on pull requests
within three business days (and, typically, one business day). We may suggest
some changes or improvements or alternatives.

Some things that will increase the chance that your pull request is accepted:

* Write tests.
* Follow the python [style guides][style].
* Write a [good commit message][commit].

[style]: https://www.python.org/dev/peps/pep-0008/
[commit]: http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html
