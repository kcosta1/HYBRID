within NHES.Systems.BalanceOfPlant.StagebyStageTurbineSecondary.Control_and_Distribution;
block Greater_der
  "Output y is true, if input u1 is greater than input u2"
  extends Modelica.Blocks.Interfaces.partialBooleanComparison;

equation
  y = der(u1) > u2;
  annotation (Icon(coordinateSystem(preserveAspectRatio=false,extent={{-100,
            -100},{100,100}}), graphics={
        Ellipse(extent={{32,10},{52,-10}}, lineColor={0,0,127}),
        Line(points={{-100,-80},{42,-80},{42,0}}, color={0,0,127}),
        Line(
          points={{-54,20},{-8,0},{-54,-20}},
          thickness=0.5)}), Documentation(info="<html>
<p>
The output is <strong>true</strong> if Real input u1 is greater than
Real input u2, otherwise the output is <strong>false</strong>.
</p>
</html>"));
end Greater_der;
