import { Image } from "expo-image";
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
  return (
    <View style={styles.panel}>
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
        source={require("./assets/course-campaign.jpg")}
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
    backgroundColor: "#142f27",
    borderColor: "#4a6959",
    borderWidth: 1,
    borderRadius: 23,
  },
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
    backgroundColor: "#142f27",
    borderColor: "#a3b1a5",
    borderWidth: 1,
  },
  dismissText: { color: "#fffaf0", fontSize: 24, lineHeight: 27 },
  title: {
    paddingRight: 41,
    color: "#fff6e8",
    fontSize: 28,
    lineHeight: 33,
    fontWeight: "800",
    letterSpacing: -0.8,
  },
  body: { color: "#d9e4d8", fontSize: 15, lineHeight: 22 },
  actions: { flexDirection: "row", flexWrap: "wrap", alignItems: "center", gap: 10, marginTop: 3 },
  action: {
    minHeight: 44,
    justifyContent: "center",
    backgroundColor: "#f6d9a9",
    borderRadius: 12,
    paddingVertical: 9,
    paddingHorizontal: 13,
  },
  actionText: { color: "#17362e", fontSize: 15, fontWeight: "800" },
  secondary: { minHeight: 44, justifyContent: "center" },
  secondaryText: {
    color: "#f6e2bd",
    fontSize: 15,
    fontWeight: "700",
    textDecorationLine: "underline",
  },
  art: { width: "100%", height: 136, backgroundColor: "#0c2219" },
  pressed: { opacity: 0.75 },
});
