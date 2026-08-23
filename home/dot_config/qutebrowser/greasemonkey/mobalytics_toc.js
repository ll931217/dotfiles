// ==UserScript==
// @name         Mobalytics Sidebar Remover & Toggleable TOC
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  Remove right sidebar and add toggleable table of contents for Mobalytics
// @author       You
// @match        https://*.mobalytics.gg/*
// @grant        none
// ==/UserScript==

(function () {
  "use strict";

  // Wait for page to load
  function waitForElement(selector, timeout = 10000) {
    return new Promise((resolve, reject) => {
      const startTime = Date.now();
      function check() {
        const element = document.querySelector(selector);
        if (element) {
          resolve(element);
        } else if (Date.now() - startTime > timeout) {
          reject(
            new Error(`Element ${selector} not found within ${timeout}ms`),
          );
        } else {
          setTimeout(check, 100);
        }
      }
      check();
    });
  }

  // CSS styles for the modifications
  const styles = `
        /* Hide the right sidebar */
        .m-0.col-xl-3.col-lg-4.d-none.d-lg-block,
        .sidebar-right,
        [class*="sidebar"][class*="right"],
        aside[class*="right"],
        .featured-builds,
        .become-creator,
        .table-of-contents-sidebar {
            display: none !important;
        }

        /* Make main content full width */
        .container-fluid .row .col-xl-9.col-lg-8,
        .main-content,
        .content-wrapper,
        [class*="col-xl-9"] {
            flex: 0 0 100% !important;
            max-width: 100% !important;
        }

        /* Floating TOC Toggle Button */
        #toc-toggle {
            position: fixed;
            top: 50%;
            right: 20px;
            transform: translateY(-50%);
            z-index: 9999;
            background: #2c3e50;
            color: white;
            border: none;
            border-radius: 50px;
            width: 50px;
            height: 50px;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            transition: all 0.3s ease;
        }

        #toc-toggle:hover {
            background: #34495e;
            transform: translateY(-50%) scale(1.1);
        }

        /* TOC Modal/Overlay */
        #toc-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 10000;
            display: none;
            align-items: center;
            justify-content: center;
        }

        #toc-modal {
            background: white;
            border-radius: 12px;
            padding: 20px;
            max-width: 400px;
            max-height: 70vh;
            width: 90%;
            overflow-y: auto;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            position: relative;
        }

        #toc-modal h3 {
            margin-top: 0;
            margin-bottom: 15px;
            color: #2c3e50;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 10px;
        }

        #toc-modal .close-btn {
            position: absolute;
            top: 15px;
            right: 20px;
            background: none;
            border: none;
            font-size: 24px;
            cursor: pointer;
            color: #7f8c8d;
        }

        #toc-modal .close-btn:hover {
            color: #e74c3c;
        }

        #toc-content {
            max-height: 50vh;
            overflow-y: auto;
        }

        #toc-content ul {
            list-style: none;
            padding: 0;
            margin: 0;
        }

        #toc-content li {
            margin: 8px 0;
        }

        #toc-content a {
            color: #3498db;
            text-decoration: none;
            display: block;
            padding: 8px 12px;
            border-radius: 6px;
            transition: all 0.2s ease;
        }

        #toc-content a:hover {
            background: #ecf0f1;
            color: #2980b9;
            text-decoration: none;
        }

        /* Smooth scrolling */
        html {
            scroll-behavior: smooth;
        }
    `;

  // Function to inject styles
  function injectStyles() {
    const styleSheet = document.createElement("style");
    styleSheet.textContent = styles;
    document.head.appendChild(styleSheet);
  }

  // Function to extract table of contents from the page
  function extractTableOfContents() {
    const toc = [];

    // Look for common heading selectors
    const headings = document.querySelectorAll(
      'h1, h2, h3, h4, h5, h6, [class*="heading"], [class*="title"]',
    );

    headings.forEach((heading, index) => {
      if (heading.textContent.trim() && heading.offsetParent !== null) {
        // Create an ID if it doesn't have one
        if (!heading.id) {
          heading.id = `heading-${index}`;
        }

        toc.push({
          text: heading.textContent.trim(),
          id: heading.id,
          level: heading.tagName.toLowerCase(),
        });
      }
    });

    return toc;
  }

  // Function to create the TOC toggle button
  function createTOCToggle() {
    const toggleBtn = document.createElement("button");
    toggleBtn.id = "toc-toggle";
    toggleBtn.innerHTML = "📋";
    toggleBtn.title = "Toggle Table of Contents";

    toggleBtn.addEventListener("click", showTOCModal);

    document.body.appendChild(toggleBtn);
  }

  // Function to create and show TOC modal
  function showTOCModal() {
    let overlay = document.getElementById("toc-overlay");

    if (!overlay) {
      overlay = document.createElement("div");
      overlay.id = "toc-overlay";

      const modal = document.createElement("div");
      modal.id = "toc-modal";

      const closeBtn = document.createElement("button");
      closeBtn.className = "close-btn";
      closeBtn.innerHTML = "✕";
      closeBtn.addEventListener("click", hideTOCModal);

      const title = document.createElement("h3");
      title.textContent = "Table of Contents";

      const content = document.createElement("div");
      content.id = "toc-content";

      modal.appendChild(closeBtn);
      modal.appendChild(title);
      modal.appendChild(content);
      overlay.appendChild(modal);
      document.body.appendChild(overlay);

      // Close on overlay click
      overlay.addEventListener("click", (e) => {
        if (e.target === overlay) {
          hideTOCModal();
        }
      });
    }

    // Update TOC content
    updateTOCContent();

    overlay.style.display = "flex";
  }

  // Function to hide TOC modal
  function hideTOCModal() {
    const overlay = document.getElementById("toc-overlay");
    if (overlay) {
      overlay.style.display = "none";
    }
  }

  // Function to update TOC content
  function updateTOCContent() {
    const content = document.getElementById("toc-content");
    if (!content) return;

    const toc = extractTableOfContents();

    if (toc.length === 0) {
      content.innerHTML = "<p>No table of contents found on this page.</p>";
      return;
    }

    const ul = document.createElement("ul");

    toc.forEach((item) => {
      const li = document.createElement("li");
      const a = document.createElement("a");
      a.href = `#${item.id}`;
      a.textContent = item.text;
      a.addEventListener("click", (e) => {
        e.preventDefault();
        const target = document.getElementById(item.id);
        if (target) {
          target.scrollIntoView({ behavior: "smooth", block: "start" });
          hideTOCModal();
        }
      });

      li.appendChild(a);
      ul.appendChild(li);
    });

    content.innerHTML = "";
    content.appendChild(ul);
  }

  // Main initialization function
  function init() {
    // Inject styles immediately
    injectStyles();

    // Wait a bit for the page to settle, then create TOC toggle
    setTimeout(() => {
      createTOCToggle();
    }, 1000);

    // Handle dynamic content loading (common on modern sites)
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.addedNodes.length > 0) {
          // Reapply styles if new content is added
          const hasNewContent = Array.from(mutation.addedNodes).some(
            (node) =>
              node.nodeType === Node.ELEMENT_NODE &&
              node.querySelector &&
              node.querySelector("h1, h2, h3, h4, h5, h6"),
          );

          if (hasNewContent) {
            // Delay to let content settle
            setTimeout(updateTOCContent, 500);
          }
        }
      });
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
    });
  }

  // Start when DOM is ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  // Also try to run after a short delay to catch dynamically loaded content
  setTimeout(init, 2000);
})();
