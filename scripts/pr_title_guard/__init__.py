"""Check pull request titles without application or network access."""

import json
import logging
import os
import re
import traceback
from pathlib import Path


class PullRequestTitleGuard:
    """Own the title decision, event reader, and process result."""

    # The lookaheads reject forbidden characters and blank fields without changing the title.
    _pattern = re.compile(
        r"(?![\s\S]*[\x00-\x1f\x7f-\x9f\u2028\u2029])"
        r"(?:fix|feat|chore|refactor|test|docs|ci|style|perf)"
        r"(?:\((?=[^()]*[^\s()])[^()]+\))?!?: "
        r"(?=\s*\S).+"
    )

    def is_valid_title(self, title: object) -> bool:
        """Return an exact Boolean without reading input or changing the title."""
        logging.info("action=%s phase=%s", "title_decision", "before")
        is_string = issubclass(type(title), str)  # A reported __class__ does not establish the real value type.
        valid = is_string and isinstance(title, str) and self._pattern.fullmatch(title) is not None
        logging.debug("action=title_decision phase=after valid=%s checked=%s", valid, int(is_string))
        return valid

    def read_title(self) -> str:
        """Read one exact title or raise a fixed input error."""
        logging.info("action=%s phase=%s", "read_event", "before")
        status = "failed"
        try:
            if not (event_path := os.environ.get("GITHUB_EVENT_PATH")):
                raise TypeError("GITHUB_EVENT_PATH is missing or empty.")
            problem = "Cannot read the GITHUB_EVENT_PATH file."  # Separate file errors from JSON errors.
            with Path(event_path).open(encoding="utf-8") as event_file:
                event_text = event_file.read()
                problem = "The GITHUB_EVENT_PATH file is not valid JSON."
                event = json.loads(event_text)
            if not isinstance(event, dict) or not isinstance(event.get("pull_request"), dict):
                raise TypeError("The event must be an object with a pull_request object.")
            title: object = event["pull_request"].get("title")
            if not isinstance(title, str):
                raise TypeError("The pull_request.title field must be a string.")
            status = "ready"
            return title
        except UnicodeDecodeError as error:
            raise TypeError("The GITHUB_EVENT_PATH file is not valid UTF-8.") from error
        except (OSError, ValueError, RecursionError) as error:
            raise TypeError(problem) from error
        finally:
            logging.debug("action=read_event phase=after status=%s checked=%s", status, int(status == "ready"))

    def check(self, title: str) -> int:
        """Print the title result and return its exit code."""
        valid = self.is_valid_title(title)
        print(f"Title: {json.dumps(title, ensure_ascii=True)}")
        if valid:
            print("Result: PASS")
        else:
            print(
                "Result: FAIL - Invalid title grammar or forbidden character.\n"
                "Use type[(scope)][!]: description.\n"
                "Allowed types: fix, feat, chore, refactor, test, docs, ci, style, perf.\n"
                "Use a nonblank scope without parentheses and a nonblank one-line description.\n"
                "Do not use control characters, Unicode line separators, or Unicode paragraph separators.\n"
                "Correct the pull request title. A title edit starts another check."
            )
        print("Checked 1 pull request title")
        return 0 if valid else 1

    def main(self) -> int:
        """Read the event and report the process result."""
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(message)s")
        try:
            title = self.read_title()
        except TypeError as error:
            source_error = error.__cause__ or error
            frames = traceback.format_tb(error.__traceback__)
            if source_error is not error:
                frames.extend(
                    traceback.format_tb(source_error.__traceback__)
                )  # Retain frames without raw error messages.
            logging.error(
                "action=read_event category=%s frames=%s",
                json.dumps(type(source_error).__name__, ensure_ascii=True),
                json.dumps("".join(frames), ensure_ascii=True),
            )
            print(f"Result: FAIL - {error}\nChecked 0 pull request titles")
            return 1
        return self.check(title)
