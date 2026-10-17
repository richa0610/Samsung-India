/**
 * Must match app.json's expo-splash-screen plugin `imageWidth`. The native
 * splash screen (shown before any JS runs) renders the logo at that fixed
 * width; every JS-rendered layer that shows the same logo during boot
 * (BrandSplash, AnimatedSplashOverlay) has to use the exact same width, or
 * the logo visibly jumps size the moment control hands off from native to
 * JS - screen-relative sizing (e.g. a percentage of screen width) only
 * matches the native fixed width by coincidence on one specific screen size.
 */
export const SPLASH_LOGO_WIDTH = 240;
export const SPLASH_LOGO_ASPECT_RATIO = 872 / 1600;
