import { Pressable, StyleSheet, Text, View } from "react-native";
import { useTranslate } from "./localization";

export function LanguageCampaign({ open, dismiss }: { open: () => void; dismiss: () => void }) {
  const t = useTranslate();
  return (
    <View style={styles.panel}>
      <View style={styles.header}>
        <View
          style={styles.scripts}
          accessible={false}
          accessibilityElementsHidden
          importantForAccessibility="no-hide-descendants"
        >
          {["Aa", "Я", "한"].map((script) => (
            <Text key={script} style={styles.symbol}>
              {script}
            </Text>
          ))}
        </View>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={t("dismissLanguageCampaign")}
          onPress={dismiss}
          style={({ pressed }) => [styles.dismiss, pressed && styles.pressed]}
        >
          <Text style={styles.dismissText}>×</Text>
        </Pressable>
      </View>
      <Text accessibilityRole="header" style={styles.title}>
        {t("languageCampaignTitle")}
      </Text>
      <Text style={styles.body}>{t("languageCampaignBody")}</Text>
      <Pressable
        accessibilityRole="button"
        onPress={open}
        style={({ pressed }) => [styles.action, pressed && styles.pressed]}
      >
        <Text style={styles.actionText}>{t("openLanguageCourses")}</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  panel: {
    backgroundColor: "#173a34",
    borderColor: "#315850",
    borderWidth: 1,
    borderRadius: 22,
    padding: 17,
    gap: 9,
  },
  header: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: 10 },
  scripts: { flexDirection: "row", gap: 5, flexShrink: 1 },
  symbol: {
    borderWidth: 1,
    borderColor: "#7ba194",
    borderRadius: 9,
    overflow: "hidden",
    backgroundColor: "#24493f",
    paddingHorizontal: 8,
    paddingVertical: 6,
    color: "#fff3dd",
    fontSize: 15,
    fontWeight: "800",
  },
  dismiss: {
    minWidth: 44,
    minHeight: 44,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 22,
    backgroundColor: "#24493f",
    borderColor: "#7ba194",
    borderWidth: 1,
  },
  dismissText: { color: "#fffaf0", fontSize: 24, lineHeight: 27 },
  title: { color: "#fffaf0", fontSize: 23, fontWeight: "800", lineHeight: 29 },
  body: { color: "#e6eee4", fontSize: 15, lineHeight: 22 },
  action: {
    alignSelf: "flex-start",
    minHeight: 44,
    justifyContent: "center",
    backgroundColor: "#f2dcc2",
    borderRadius: 12,
    paddingVertical: 9,
    paddingHorizontal: 13,
    marginTop: 4,
  },
  actionText: { color: "#183630", fontSize: 15, fontWeight: "800" },
  pressed: { opacity: 0.75 },
});
