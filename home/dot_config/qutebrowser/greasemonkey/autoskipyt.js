// ==UserScript==
// @name         Auto Skip YouTube Ads
// @version      1.1.0
// @description  Speed up and skip YouTube ads automatically
// @author       jso8910
// @match        *://*.youtube.com/*
// @exclude      *://*.youtube.com/subscribe_embed?*
// ==/UserScript==
// setInterval(() => {
//   const btn = document.querySelector(
//     ".videoAdUiSkipButton,.ytp-ad-skip-button",
//   );
//   if (btn) {
//     btn.click();
//   }
//   const ad = [...document.querySelectorAll(".ad-showing")][0];
//   if (ad) {
//     const video = document.querySelector("video");
//     video.muted = true;
//     video.hidden = true;
//
//     // This is not necessarily available right at the start
//     if (video.duration != NaN) {
//       video.currentTime = video.duration;
//     }
//
//     // 16 seems to be the highest rate that works, mostly this isn't needed
//     video.playbackRate = 16;
//   }
// }, 50);

// ==UserScript==
// u/name Skip YouTube ads
// u/description Skips the ads in YouTube videos
// u/run-at document-start
// u/include *.youtube.com/*
// ==/UserScript==

document.addEventListener(
  "load",
  () => {
    const btn = document.querySelector(
      ".videoAdUiSkipButton,.ytp-ad-skip-button-modern",
    );
    if (btn) {
      btn.click();
    }
    const ad = [...document.querySelectorAll(".ad-showing")][0];
    if (ad) {
      document.querySelector("video").currentTime = 9999999999;
    }
  },
  true,
);
