import type { LogicMap } from "@/lib/types";
import ConfidenceBadge from "./ConfidenceBadge";
import styles from "./LogicMapView.module.css";

interface Props {
  logicMap: LogicMap;
}

export default function LogicMapView({ logicMap }: Props) {
  return (
    <div className={styles.wrapper}>
      {/* Executive Summary */}
      <section className={styles.section}>
        <h3 className={styles.sectionTitle}>Executive Summary</h3>
        <p className={styles.text}>{logicMap.executive_summary}</p>
      </section>

      {/* Business Objective */}
      <section className={styles.section}>
        <h3 className={styles.sectionTitle}>Business Objective</h3>
        <p className={styles.text}>{logicMap.business_objective}</p>
      </section>

      {/* Business Rules */}
      {logicMap.business_rules.length > 0 && (
        <section className={styles.section}>
          <h3 className={styles.sectionTitle}>
            Business Rules
            <span className={styles.count}>{logicMap.business_rules.length}</span>
          </h3>
          <ul className={styles.list}>
            {logicMap.business_rules.map((rule, i) => (
              <li key={i}>{rule}</li>
            ))}
          </ul>
        </section>
      )}

      {/* Critical Constraints */}
      {logicMap.critical_constraints.length > 0 && (
        <section className={styles.section}>
          <h3 className={styles.sectionTitle}>
            Critical Constraints
            <span className={styles.count}>{logicMap.critical_constraints.length}</span>
          </h3>
          <ul className={styles.list}>
            {logicMap.critical_constraints.map((c, i) => (
              <li key={i} className={styles.constraint}>{c}</li>
            ))}
          </ul>
        </section>
      )}

      {/* Edge Cases */}
      {logicMap.edge_cases.length > 0 && (
        <section className={styles.section}>
          <h3 className={styles.sectionTitle}>
            Edge Cases
            <span className={styles.count}>{logicMap.edge_cases.length}</span>
          </h3>
          <ul className={styles.list}>
            {logicMap.edge_cases.map((e, i) => (
              <li key={i}>{e}</li>
            ))}
          </ul>
        </section>
      )}

      {/* Logic Flow */}
      {logicMap.step_by_step_logic_flow.length > 0 && (
        <section className={styles.section}>
          <h3 className={styles.sectionTitle}>Logic Flow</h3>
          <ol className={styles.orderedList}>
            {logicMap.step_by_step_logic_flow.map((step, i) => (
              <li key={i}>{step}</li>
            ))}
          </ol>
        </section>
      )}

      {/* Dependencies */}
      {logicMap.dependencies && logicMap.dependencies.length > 0 && (
        <section className={styles.section}>
          <h3 className={styles.sectionTitle}>
            Macro Dependencies
            <span className={styles.count}>{logicMap.dependencies.length}</span>
          </h3>
          <ul className={styles.list}>
            {logicMap.dependencies.map((dep, i) => (
              <li key={i} className={styles.dependencyItem}>
                <span className={styles.depName}>{dep.reference_name}</span>
                {dep.status === "unresolved" ? (
                  <span className={styles.statusUnresolved}>⚠ Unresolved</span>
                ) : (
                  <span className={styles.statusResolved}>✓ {dep.resolved_filename}</span>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* I/O */}
      <section className={styles.section}>
        <h3 className={styles.sectionTitle}>Inputs &amp; Outputs</h3>
        <div className={styles.ioGrid}>
          <div>
            <h4 className={styles.subTitle}>Inputs</h4>
            <ul className={styles.list}>
              {logicMap.inputs_and_outputs.inputs.map((inp, i) => (
                <li key={i}>{inp}</li>
              ))}
            </ul>
          </div>
          <div>
            <h4 className={styles.subTitle}>Outputs</h4>
            <ul className={styles.list}>
              {logicMap.inputs_and_outputs.outputs.map((out, i) => (
                <li key={i}>{out}</li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      {/* Confidence Assessment */}
      <section className={styles.section}>
        <h3 className={styles.sectionTitle}>
          Analyst Confidence
          <ConfidenceBadge level={logicMap.confidence_assessment.level} />
        </h3>
        <p className={styles.text}>{logicMap.confidence_assessment.rationale}</p>
      </section>
    </div>
  );
}
