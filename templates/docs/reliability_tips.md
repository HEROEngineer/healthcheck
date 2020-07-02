# Pinging Reliability Tips

Sending monitoring signals over public internet is inherently unreliable.
HTTP requests can sometimes take excessively long or fail completely
for a variety of reasons. Here are some general tips to make your monitoring
code more robust.

## Specify HTTP Request Timeout

Put a time limit on how long each ping is allowed to take. This is especially
important when sending a "start" signal at the start of a job: you don't want
a stuck ping prevent the actual job from running. Another case is a continuously
running worker process which pings SITE_NAME after each completed item. A stuck
request would block the whole process, so it is important to guard against.

Specifying the timeout depends on the tool you use. curl, for example, has the
`--max-time` (shorthand: `-m`) parameter:

```bash
# Send a HTTP, 10 second timeout:
curl -m 10 PING_URL
```

## Use Retries

To minimize the amount of false alerts you get from SITE_NAME, instruct your HTTP
client to retry failed requests several times.

Specifying the retry policy depends on the tool you use. curl, for example, has the
`--retry` parameter:

```bash
# Retry up to 5 times, uses an increasing delay between each retry (1s, 2s, 4s, 8s, ...)
curl --retry 5 PING_URL
```

## Handle Exceptions

Make sure you know how your HTTP client handles failed requests. For example,
if you use a HTTP library which raises exceptions, decide if you want to
catch the exceptions, or let them bubble up.
