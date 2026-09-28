---
name: post-listing
description: Use when a checked listing exists and the owner wants it entered into the marketplace's sell form in their logged-in Chrome. Fills fields and uploads photos, then stops for the owner to review and submit.
---

# Post listing

Fills the marketplace's sell form from `listings/<marketplace>.md` and
`photos/web/`. Expects status `priced` with a listing that passes
`check-listing`. Ends at `listed` after the owner confirms they posted.

You never click Post, Publish, List it, or any equivalent. The owner does.

## Gate

Run `uv run classifieds validate items/<slug>` and
`uv run classifieds check-listing items/<slug> <marketplace>`. Both must
print `ok`. Read `marketplaces/<marketplace>.md` in full, especially
"Posting flow" and "Gotchas".

## Browser setup

Load the Chrome tools in one ToolSearch call: tabs_context_mcp, navigate,
computer, read_page, find, form_input, file_upload, tabs_create_mcp,
tabs_close_mcp. Call tabs_context_mcp first, then create a new tab. Do not
reuse existing tabs.

## Fill the form

Follow the profile's posting flow step by step. For each step, find the
field, set it from the matching frontmatter key, and confirm the value
took by reading the page back.

If the live form differs from the profile (a field is missing, named
differently, has different options, or a limit differs):

1. Stop filling.
2. Report the exact difference to the owner.
3. Update the profile file: fix the frontmatter value or option list and
   add a line under "Gotchas". Remove the `unverified` marker for any
   value you have now confirmed.
4. If the difference changes the listing (an option value, a length), fix
   `listings/<marketplace>.md`, rerun `check-listing`, then continue.

Upload photos from `photos/web/` in name order using file_upload. Confirm
the count on the page matches.

Paste the description body verbatim.

## Hand off

Take a screenshot of the filled form. Tell the owner: the form is filled,
here is what to check, and they should click Post when satisfied. Wait.

When the owner says it is posted, ask for the listing URL, then run:

`uv run classifieds status items/<slug> listed --note <url>`

If `marketplaces` in item.md does not include this marketplace, add it
before running the status command, or the validation gate will reject
the transition. Show the command output.
