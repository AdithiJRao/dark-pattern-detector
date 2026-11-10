chrome.runtime.onMessage.addListener((msg, sender) => {
  if (msg.type === "COUNT" && sender.tab) {
    chrome.action.setBadgeText({ text: msg.count ? String(msg.count) : "", tabId: sender.tab.id });
    chrome.action.setBadgeBackgroundColor({ color: "#d00", tabId: sender.tab.id });
  }
});