(() => {
    "use strict";

    const body = document.body;

    const menuButton = document.getElementById(
        "mobileMenuButton",
    );

    const overlay = document.getElementById(
        "mobileOverlay",
    );

    const sidebar = document.getElementById(
        "portalSidebar",
    );

    const closeSidebar = () => {
        body.classList.remove(
            "sidebar-open",
        );
    };

    const openSidebar = () => {
        body.classList.add(
            "sidebar-open",
        );
    };

    if (menuButton) {
        menuButton.addEventListener(
            "click",
            () => {
                if (
                    body.classList.contains(
                        "sidebar-open",
                    )
                ) {
                    closeSidebar();
                } else {
                    openSidebar();
                }
            },
        );
    }

    if (overlay) {
        overlay.addEventListener(
            "click",
            closeSidebar,
        );
    }

    if (sidebar) {
        sidebar
            .querySelectorAll("a")
            .forEach((link) => {
                link.addEventListener(
                    "click",
                    () => {
                        if (
                            window.innerWidth
                            <= 860
                        ) {
                            closeSidebar();
                        }
                    },
                );
            });
    }

    window.addEventListener(
        "keydown",
        (event) => {
            if (event.key === "Escape") {
                closeSidebar();
            }
        },
    );
})();