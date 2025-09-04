<template>
	<div
		:class="[
			'inline-flex items-center px-3 py-1 rounded-full text-sm font-medium',
			getStreakColor(),
			size === 'sm' ? 'px-2 py-1 text-xs' :
			size === 'lg' ? 'px-4 py-2 text-base' : ''
		]"
	>
		<span class="mr-1">{{ getStreakEmoji() }}</span>
		<span>{{ streak }}</span>
		<span class="ml-1 opacity-75">{{ streak === 1 ? 'day' : 'days' }}</span>
	</div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
	streak: {
		type: Number,
		required: true
	},
	size: {
		type: String,
		default: 'md',
		validator: (value) => ['sm', 'md', 'lg'].includes(value)
	},
	showAnimation: {
		type: Boolean,
		default: false
	}
})

const getStreakColor = () => {
	if (props.streak === 0) {
		return 'bg-gray-100 text-gray-600'
	} else if (props.streak < 7) {
		return 'bg-orange-100 text-orange-700'
	} else if (props.streak < 30) {
		return 'bg-red-100 text-red-700'
	} else if (props.streak < 100) {
		return 'bg-purple-100 text-purple-700'
	} else {
		return 'bg-yellow-100 text-yellow-700'
	}
}

const getStreakEmoji = () => {
	if (props.streak === 0) {
		return '💤'
	} else if (props.streak < 7) {
		return '🔥'
	} else if (props.streak < 30) {
		return '⚡'
	} else if (props.streak < 100) {
		return '🚀'
	} else {
		return '👑'
	}
}
</script>

<style scoped>
@keyframes pulse-glow {
	0%, 100% {
		transform: scale(1);
		opacity: 1;
	}
	50% {
		transform: scale(1.05);
		opacity: 0.8;
	}
}

.animate-pulse-glow {
	animation: pulse-glow 2s ease-in-out infinite;
}
</style>