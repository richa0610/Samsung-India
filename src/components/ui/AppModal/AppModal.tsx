import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Animated,
  Dimensions,
  KeyboardAvoidingView,
  Modal,
  Platform,
  Pressable,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import ModalHeader from "./ModalHeader";
import { styles } from "./styles";
import { AppModalProps } from "./types";

const { width, height } = Dimensions.get("window");

const alignStyleForPosition = {
  bottom: "alignBottom",
  top: "alignTop",
  left: "alignLeft",
  right: "alignRight",
  center: "alignCenter",
} as const;

export default function AppModal({
  visible,
  onClose,
  children,
  title,
  subtitle,
  showCloseButton,
  position = "center",
  overlayOpacity = 0.4,
  animationDuration = 300,
  closeOnOverlayPress = true,
  containerStyle,
  contentStyle,
}: AppModalProps) {
  const insets = useSafeAreaInsets();
  const [isMounted, setIsMounted] = useState(visible);

  if (visible && !isMounted) {
    setIsMounted(true);
  }

  const translate = useMemo(() => new Animated.Value(0), []);
  const opacity = useMemo(() => new Animated.Value(0), []);
  const scale = useMemo(() => new Animated.Value(0.9), []);

  const getInitialValue = useCallback(() => {
    switch (position) {
      case "bottom":
        return height;

      case "top":
        return -height;

      case "left":
        return -width;

      case "right":
        return width;

      default:
        return 0;
    }
  }, [position]);

  useEffect(() => {
    const useNativeDriver = Platform.OS !== "web";

    if (visible) {
      translate.setValue(getInitialValue());
      opacity.setValue(0);
      scale.setValue(0.9);

      Animated.parallel([
        Animated.timing(translate, {
          toValue: 0,
          duration: animationDuration,
          useNativeDriver,
        }),

        Animated.timing(opacity, {
          toValue: 1,
          duration: animationDuration,
          useNativeDriver,
        }),

        Animated.spring(scale, {
          toValue: 1,
          useNativeDriver,
        }),
      ]).start();
    } else if (isMounted) {
      Animated.parallel([
        Animated.timing(translate, {
          toValue: getInitialValue(),
          duration: animationDuration,
          useNativeDriver,
        }),

        Animated.timing(opacity, {
          toValue: 0,
          duration: animationDuration,
          useNativeDriver,
        }),

        Animated.timing(scale, {
          toValue: 0.9,
          duration: animationDuration,
          useNativeDriver,
        }),
      ]).start(() => {
        setIsMounted(false);
      });
    }
  }, [visible, isMounted, animationDuration, getInitialValue, opacity, scale, translate]);

  if (!isMounted) return null;

  const transform = [];

  if (position === "left" || position === "right") {
    transform.push({
      translateX: translate,
    });
  }

  if (position === "top" || position === "bottom") {
    transform.push({
      translateY: translate,
    });
  }

  if (position === "center") {
    transform.push({
      scale,
    });
  }

  return (
    <Modal transparent visible={isMounted} onRequestClose={onClose}>
      <View style={[styles.container, containerStyle]}>
        <Pressable
          style={[
            styles.overlay,
            {
              backgroundColor: `rgba(0,0,0,${overlayOpacity})`,
            },
          ]}
          onPress={() => {
            if (closeOnOverlayPress) {
              onClose();
            }
          }}
        />

        <KeyboardAvoidingView
          style={[styles.keyboard, styles[alignStyleForPosition[position]]]}
          behavior="padding"
          pointerEvents="box-none"
        >
          <Animated.View
            style={[
              styles.content,
              styles[position],
              // Keep a centered modal within the visible screen (status bar +
              // gesture/nav bar excluded) so tall content scrolls instead of
              // spilling off both edges.
              position === "center" && {
                maxHeight: height - insets.top - insets.bottom - 24,
              },
              contentStyle,
              {
                opacity,
                transform,
              },
            ]}
          >
            {title && (
              <ModalHeader
                title={title}
                subtitle={subtitle}
                onClose={onClose}
                showCloseButton={showCloseButton}
              />
            )}
            {children}
            {/* Clears the device's gesture/nav bar so bottom-sheet content
                (e.g. the last row of a long list) is never obscured by it. */}
            {position === "bottom" && <View style={{ height: insets.bottom }} />}
          </Animated.View>
        </KeyboardAvoidingView>
      </View>
    </Modal>
  );
}
