# Input Reader Contract

## Shared reader

`AsciiWholeNumberReader(maximum, field).read(text)` accepts nonempty ASCII decimal text.
The immutable reader owns the caller's number bound and diagnostic field name.
It validates representation length before integer conversion or leading zero removal.
It validates significant decimal length and value against `maximum` before conversion.
It returns `None` for an invalid field and records a safe diagnostic.
The diagnostic states `checked=1`, the field, the reason, and the character count.

The caller supplies the number bound.
The backend supplies the representation bound.
No caller changes the system integer limit.

## Organization picker

`GET /select/org?offset=<text>&q=<filter>` keeps its existing authentication rule.
A damaged offset returns status 200 and the first filtered page.
A valid offset past the current row count still shows the empty final page.
One leading plus sign, leading zeros, and surrounding whitespace remain valid.
Several plus signs remain invalid.

## Capture start

`POST /api/sites/<site_id>/captures` accepts the existing JSON and form body shapes.
An invalid text tier returns exactly:

```json
{
  "error": {
    "code": "bad_tier",
    "message": "Choose the data tier 2 or the data tier 3."
  }
}
```

The status is 400.
The refusal occurs before capture conflict checks, capture launch, or firmware work.
The existing sign-in and site scope refusals still occur first.
An absent tier still means tier 2.
Booleans, floats, signs, and surrounding whitespace remain invalid tier values.

## Client page limit

`MIST_PAGE_LIMIT` uses the existing named fallback for invalid text.
Valid zero still means `MIN_PAGE_LIMIT`.
Valid values above `MAX_PAGE_LIMIT` still produce the upper bound.
The setting reader itself opens no network connection.
