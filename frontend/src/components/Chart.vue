<script setup lang="ts">
import { computed } from "vue";
import VChart from "vue-echarts";
import { use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { BarChart } from "echarts/charts";
import { GridComponent, TooltipComponent } from "echarts/components";

use([CanvasRenderer, BarChart, GridComponent, TooltipComponent]);

const props = defineProps<{ config: any }>();

const option = computed(() => ({
  xAxis: {
    type: "category",
    data: props.config.data.map((d: any) => d[props.config.x_key]),
  },
  yAxis: { type: "value" },
  series: [
    {
      data: props.config.data.map((d: any) => d[props.config.y_key]),
      type: "bar",
    },
  ],
}));
</script>

<template>
  <div class="mt-2">
    <VChart :option="option" autoresize style="height: 250px" />
  </div>
</template>
