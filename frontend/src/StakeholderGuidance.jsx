const GROUPS = [
  {
    icon: "🏛️",
    title: "Policymakers",
    subtitle: "Government / Institutions",
    color: "#9B59D0",
    goal: "Stabilise system + prevent panic",
    actions: [
      {
        text: "Activate ",
        bold: "buffer stock release",
        suffix: " (e.g. food, fuel reserves)",
      },
      { text: "Diversify imports / reroute supply chains early" },
      { text: "Implement ", bold: "temporary price controls or subsidies" },
      { text: "Communicate clear guidance to avoid misinformation" },
    ],
    keyIdea: "system-level intervention",
  },
  {
    icon: "🏢",
    title: "Businesses",
    subtitle: "Suppliers / Retailers",
    color: "#18A87A",
    goal: "Maintain operations + manage risk",
    actions: [
      { text: "Increase inventory for critical goods" },
      { text: "Identify alternative suppliers or logistics routes" },
      { text: "Adjust pricing strategies gradually (avoid shock spikes)" },
      { text: "Prepare contingency plans for demand surges" },
    ],
    keyIdea: "operational adaptation",
  },
  {
    icon: "👥",
    title: "Citizens",
    subtitle: "General Public",
    color: "#3090E8",
    goal: "Reduce panic + ensure personal stability",
    actions: [
      {
        text: "Stock up on ",
        bold: "essential items only",
        suffix: " (avoid hoarding)",
      },
      { text: "Shift to substitute goods if shortages occur" },
      { text: "Stay informed through verified sources" },
      { text: "Reduce unnecessary consumption during uncertainty" },
    ],
    keyIdea: "behavioral response",
  },
];

function ActionItem({ action }) {
  if (action.bold) {
    return (
      <div
        style={{
          display: "flex",
          alignItems: "flex-start",
          gap: 8,
          marginBottom: 6,
        }}
      >
        <span
          style={{
            color: "rgba(45,58,82,0.3)",
            fontSize: 11,
            lineHeight: "20px",
            flexShrink: 0,
          }}
        >
          •
        </span>
        <span
          style={{
            fontSize: 12,
            color: "rgba(45,58,82,0.75)",
            lineHeight: 1.55,
          }}
        >
          {action.text}
          <strong style={{ color: "rgba(45,58,82,0.9)", fontWeight: 700 }}>
            {action.bold}
          </strong>
          {action.suffix || ""}
        </span>
      </div>
    );
  }
  return (
    <div
      style={{
        display: "flex",
        alignItems: "flex-start",
        gap: 8,
        marginBottom: 6,
      }}
    >
      <span
        style={{
          color: "rgba(45,58,82,0.3)",
          fontSize: 11,
          lineHeight: "20px",
          flexShrink: 0,
        }}
      >
        •
      </span>
      <span
        style={{ fontSize: 12, color: "rgba(45,58,82,0.75)", lineHeight: 1.55 }}
      >
        {action.text}
      </span>
    </div>
  );
}

export default function StakeholderGuidance({ animDelay = 0 }) {
  return (
    <div
      style={{
        background: "#FDFCFA",
        border: "1px solid rgba(45,58,82,0.1)",
        borderRadius: 14,
        overflow: "hidden",
        marginTop: 20,
        animation: `panelIn 0.4s cubic-bezier(0.4,0,0.2,1) ${animDelay}s both`,
      }}
    >
      {/* Top colour bar */}
      <div
        style={{
          height: 3,
          background: "linear-gradient(to right, #9B59D0, #18A87A, #3090E8)",
        }}
      />

      <div style={{ padding: "14px 16px" }}>
        {/* Section label */}
        <div
          style={{
            fontSize: 9,
            fontWeight: 800,
            color: "rgba(45,58,82,0.32)",
            textTransform: "uppercase",
            letterSpacing: "0.12em",
            marginBottom: 14,
          }}
        >
          Stakeholder Guidance
        </div>

        {/* Cards row */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
            gap: 10,
          }}
        >
          {GROUPS.map((group) => (
            <div
              key={group.title}
              style={{
                border: `1px solid ${group.color}33`,
                borderRadius: 12,
                background: `${group.color}0A`,
                padding: "12px 13px",
                display: "flex",
                flexDirection: "column",
              }}
            >
              {/* Header */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  marginBottom: 6,
                }}
              >
                <span style={{ fontSize: 18 }}>{group.icon}</span>
                <div>
                  <div
                    style={{
                      fontSize: 13,
                      fontWeight: 800,
                      color: "rgba(45,58,82,0.92)",
                      letterSpacing: "-0.01em",
                      lineHeight: 1.2,
                    }}
                  >
                    {group.title}
                  </div>
                  <div
                    style={{
                      fontSize: 10,
                      color: group.color,
                      fontWeight: 600,
                    }}
                  >
                    {group.subtitle}
                  </div>
                </div>
              </div>

              {/* Goal */}
              <div
                style={{
                  fontSize: 11,
                  fontWeight: 700,
                  color: "rgba(45,58,82,0.75)",
                  marginBottom: 10,
                  paddingBottom: 8,
                  borderBottom: `1px solid ${group.color}22`,
                }}
              >
                Goal: {group.goal}
              </div>

              {/* Actions */}
              <div style={{ flex: 1 }}>
                {group.actions.map((action, i) => (
                  <ActionItem key={i} action={action} />
                ))}
              </div>

              {/* Key idea */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                  marginTop: 10,
                  paddingTop: 8,
                  borderTop: `1px solid ${group.color}22`,
                }}
              >
                <span style={{ fontSize: 13 }}>👉</span>
                <span
                  style={{
                    fontSize: 11,
                    color: "rgba(45,58,82,0.5)",
                  }}
                >
                  Key idea:{" "}
                  <em
                    style={{ color: "rgba(45,58,82,0.7)", fontStyle: "italic" }}
                  >
                    {group.keyIdea}
                  </em>
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
