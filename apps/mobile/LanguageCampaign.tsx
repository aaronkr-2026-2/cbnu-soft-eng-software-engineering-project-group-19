import { Image } from "expo-image";
import { useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useTranslate } from "./localization";

export function LanguageCampaign({
  openAll,
  openLanguages,
  dismiss,
}: {
  openAll: () => void;
  openLanguages: () => void;
  dismiss: () => void;
}) {
  const t = useTranslate();
  const [hovered, setHovered] = useState(false);
  return (
    <View
      onPointerEnter={() => setHovered(true)}
      onPointerLeave={() => setHovered(false)}
      style={[styles.panel, hovered && styles.panelHovered]}
    >
      <View style={styles.copy}>
        <Text accessibilityRole="header" style={styles.title}>
          {t("languageCampaignTitle")}
        </Text>
        <Text style={styles.body}>{t("languageCampaignBody")}</Text>
        <View style={styles.actions}>
          <Pressable
            accessibilityRole="button"
            onPress={openAll}
            style={({ pressed }) => [styles.action, pressed && styles.pressed]}
          >
            <Text style={styles.actionText}>{t("openCampaignCatalog")}</Text>
          </Pressable>
          <Pressable
            accessibilityRole="button"
            onPress={openLanguages}
            style={({ pressed }) => [styles.secondary, pressed && styles.pressed]}
          >
            <Text style={styles.secondaryText}>{t("openLanguageCourses")}</Text>
          </Pressable>
        </View>
      </View>
      <Image
        accessibilityElementsHidden
        importantForAccessibility="no"
        source={require("./assets/academy-study.jpg")}
        contentFit="cover"
        contentPosition="center"
        style={styles.art}
      />
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={t("dismissLanguageCampaign")}
        onPress={dismiss}
        style={({ pressed }) => [styles.dismiss, pressed && styles.pressed]}
      >
        <Text style={styles.dismissText}>×</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  panel: {
    overflow: "hidden",
    backgroundColor: "#b3c4b0",
    borderColor: "#96a995",
    borderWidth: 1,
    borderRadius: 23,
  },
  panelHovered: { borderColor: "#87a58d" },
  copy: { gap: 10, padding: 18 },
  dismiss: {
    position: "absolute",
    top: 9,
    right: 9,
    width: 44,
    height: 44,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 22,
    backgroundColor: "#b3c4b0",
    borderColor: "#a3b1a5",
    borderWidth: 1,
  },
  dismissText: { color: "#263d30", fontSize: 24, lineHeight: 27 },
  title: {
    paddingRight: 41,
    color: "#23382d",
    fontSize: 28,
    lineHeight: 33,
    fontWeight: "800",
    letterSpacing: -0.8,
  },
  body: { color: "#3e5648", fontSize: 15, lineHeight: 22 },
  actions: { flexDirection: "row", flexWrap: "wrap", alignItems: "center", gap: 10, marginTop: 3 },
  action: {
    minHeight: 44,
    justifyContent: "center",
    backgroundColor: "#a14f2d",
    borderRadius: 12,
    paddingVertical: 9,
    paddingHorizontal: 13,
  },
  actionText: { color: "#fffdf5", fontSize: 15, fontWeight: "800" },
  secondary: { minHeight: 44, justifyContent: "center" },
  secondaryText: {
    color: "#2d533c",
    fontSize: 15,
    fontWeight: "700",
    textDecorationLine: "underline",
  },
  art: { width: "100%", height: 160, backgroundColor: "#e7eddf" },
  pressed: { opacity: 0.75 },
});
