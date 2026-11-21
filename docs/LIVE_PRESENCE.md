# Live browser count

The eye badge counts browser sessions active on the MovieBox Projects pages within the last **90 seconds**. Visible pages send a heartbeat every 25 seconds. It is not a count of unique people, installs, app viewers or lifetime visits.

- One random browser ID is shared across tabs through browser-local storage. Web Locks prevents supported browsers creating duplicate IDs simultaneously.
- A browser receives a short-lived server-signed token. The backend validates its origin and token before renewing its presence.
- Hidden pages stop sending heartbeats. With no other visible tab, the browser drops out of the count after 90 seconds.
- The site stores an anonymous ID, token and expiry locally. After 30 minutes without activity a new ID is used. This ID is not linked to the apps or download history.
- The service database contains only the random ID and expiry. Expired rows are removed on subsequent count/heartbeat requests. The application stores no IP addresses, names, email addresses or page history. Hosting providers process normal HTTP requests and may keep operational logs.
- When the service fails, the badge shows a dash, never an invented count. Preview/local, automated WebDriver and `?presence=off` visits are excluded. Site QA intercepts requests; release assets are never downloaded to test this counter.
- Multiple devices, blocked local storage, private windows, browser restrictions, robots that simulate activity and network delays prevent an exact human headcount. Origin and signed-token checks are not proof that a visitor is human.

The deployed backend source is mirrored in [services/presence](../services/presence/). Its hosting configuration is maintained in the MovieBox Live Presence Sites source repository. Production endpoint: `https://moviebox-live-presence-emran.superannotat-0952.chatgpt.site`. It uses a Cloudflare Worker and D1, separate from GitHub Pages and GitHub's download counters. The HMAC signing key exists only in the backend's secret environment, never in this website.
