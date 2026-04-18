# Floosy Auth & Cloud Strategy

_Last updated: 2026-04-18_

## Current Beta Decision

For the current private beta, Floosy will continue using Supabase email/password login.

This is enough for the first real usage month because the priority is to validate:

- Core daily money tracking flows.
- Monthly commitments and proof attachments.
- Cloud save/load reliability.
- Real feedback from actual users before adding more account options.

## Recommended Beta Usage

Use one account per tester.

Each tester should:

- Sign up or sign in from **Settings > Cloud**.
- Save their own data with **Save My Data**.
- Load their own data with **Load My Data** when switching devices.
- Export a JSON backup regularly during beta.

## Next Authentication Upgrade

After the beta flow is stable, add:

- **Continue with Apple**
- **Continue with Google**

These should be login methods, not separate storage systems.

The goal is to make Floosy feel familiar and trustworthy like modern apps, while still keeping one backend source of truth.

## Data Storage Direction

Recommended direction:

- Keep user data in Floosy's backend, currently Supabase.
- Use Apple/Google only as trusted sign-in providers.
- Keep the app able to work across web, iPhone, Android, and desktop.
- Keep export/backup available even after Apple/Google login is added.

This means Apple/Google identify the user, but Floosy still owns the product data model.

## Why Not iCloud First

iCloud sync can be considered later if Floosy becomes a native iOS app.

It is not the first priority because:

- It mainly helps Apple users.
- It does not naturally support Android and web users.
- Floosy may need subscriptions, support, multi-device sync, and account recovery across platforms.

## Future Security Requirements

Before public launch, review:

- Clear privacy and terms language.
- Strong password/account recovery flow.
- Optional Apple/Google sign-in.
- Data export and delete controls.
- Cloud status that clearly shows saved, not saved, or setup needed.
- Sensitive data handling for attachments and proof files.

## Decision Summary

Now:

- Supabase email/password for beta.
- Real usage testing for one month.
- Weekly export backups.

Later:

- Add Apple/Google sign-in.
- Keep Supabase or similar backend as the main data store.
- Consider iCloud only if Floosy becomes a native iOS-first app.
